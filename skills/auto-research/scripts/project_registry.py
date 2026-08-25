#!/usr/bin/env python3
"""Maintain local GitHub-repository to ChatGPT-conversation bindings."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any


REGISTRY_VERSION = 1


class RegistryError(RuntimeError):
    pass


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def registry_path() -> Path:
    configured = os.environ.get("CODEX_HOME")
    codex_root = Path(configured).expanduser() if configured else Path.home() / ".codex"
    return (codex_root / "auto-research" / "targets.json").resolve()


def canonical_github_remote(remote: str) -> str:
    value = remote.strip()
    if not value:
        raise RegistryError("Git remote.origin.url is empty")
    scp_match = re.fullmatch(
        r"(?:(?P<username>[^@\s]+)@)?github\.com:(?P<path>[^\s]+)",
        value,
        flags=re.IGNORECASE,
    )
    if scp_match:
        username = scp_match.group("username")
        if username and username.casefold() != "git":
            raise RegistryError("GitHub SCP-style origin must use the git SSH username")
        path = scp_match.group("path")
    else:
        try:
            parsed = urllib.parse.urlparse(value)
        except ValueError as exc:
            raise RegistryError(f"Invalid GitHub remote URL: {exc}") from exc
        if parsed.scheme.lower() not in {"http", "https", "ssh", "git"}:
            raise RegistryError("GitHub origin must use http(s), ssh, git, or SCP-style syntax")
        if (parsed.hostname or "").lower() != "github.com":
            raise RegistryError("auto-research currently requires a github.com origin remote")
        if parsed.password or (
            parsed.username
            and (parsed.scheme.lower() in {"http", "https"} or parsed.username != "git")
        ):
            raise RegistryError("GitHub remote URL must not embed credentials or tokens")
        path = parsed.path.lstrip("/")
    path = re.sub(r"\.git$", "", path, flags=re.IGNORECASE).strip("/")
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        raise RegistryError("GitHub origin must identify exactly owner/repository")
    owner, repository = (part.casefold() for part in parts)
    return f"github.com/{owner}/{repository}"


def canonical_conversation_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise RegistryError(f"Invalid ChatGPT conversation URL: {exc}") from exc
    if parsed.scheme not in {"http", "https"} or not (
        host == "chatgpt.com" or host.endswith(".chatgpt.com")
    ):
        raise RegistryError("Conversation URL must use http(s) on chatgpt.com")
    if parsed.username or parsed.password:
        raise RegistryError("Conversation URL must not contain credentials")
    if port not in {None, 80, 443}:
        raise RegistryError("Conversation URL must not use a custom port")
    path = re.sub(r"/+$", "", parsed.path or "") or "/"
    if "/c/" not in path:
        raise RegistryError("Conversation URL must identify a ChatGPT /c/ conversation")
    return urllib.parse.urlunsplit(("https", host, path, "", ""))


def git_output(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RegistryError("Could not inspect the requested Git repository")
    return completed.stdout.strip()


def repository_identity(repo_value: str) -> tuple[Path, str]:
    requested = Path(repo_value).expanduser().resolve()
    root_value = git_output(requested, "rev-parse", "--show-toplevel")
    root = Path(root_value).resolve()
    remote = git_output(root, "config", "--get", "remote.origin.url")
    return root, canonical_github_remote(remote)


def empty_registry() -> dict[str, Any]:
    return {"version": REGISTRY_VERSION, "projects": {}}


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_registry()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Could not read registry: {exc}") from exc
    if not isinstance(value, dict) or value.get("version") != REGISTRY_VERSION:
        raise RegistryError(f"Unsupported registry schema in {path}")
    if not isinstance(value.get("projects"), dict):
        raise RegistryError(f"Registry projects value is invalid in {path}")
    return value


def write_registry(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".targets.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
        path.chmod(0o600)
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def require_entry(registry: dict[str, Any], repo_key: str) -> dict[str, Any]:
    entry = registry["projects"].get(repo_key)
    if not isinstance(entry, dict):
        raise RegistryError(f"No auto-research binding exists for {repo_key}")
    return entry


def command_bind(args: argparse.Namespace, path: Path) -> None:
    root, repo_key = repository_identity(args.repo)
    environment = " ".join(args.environment.split())
    title = " ".join(args.conversation_title.split())
    model_label = " ".join(args.model_label.split())
    if not environment or not title or not model_label:
        raise RegistryError("Environment, conversation title, and model label must be non-empty")
    conversation_url = canonical_conversation_url(args.conversation_url)
    registry = load_registry(path)
    projects = registry["projects"]
    existing = projects.get(repo_key)
    desired_identity = {
        "environment": environment,
        "conversation_url": conversation_url,
        "conversation_title": title,
        "model_label": model_label,
    }
    for other_key, other_entry in list(projects.items()):
        if other_key == repo_key or not isinstance(other_entry, dict):
            continue
        if other_entry.get("conversation_url") == conversation_url:
            if not args.replace:
                raise RegistryError(
                    f"Conversation is already bound to {other_key}; use --replace to reassign it"
                )
            del projects[other_key]
    if isinstance(existing, dict):
        current_identity = {key: existing.get(key) for key in desired_identity}
        if current_identity != desired_identity and not args.replace:
            raise RegistryError(f"Binding already exists for {repo_key}; use --replace to change it")
        bound_at = existing.get("bound_at") or timestamp()
    else:
        bound_at = timestamp()
    projects[repo_key] = {
        **desired_identity,
        "bound_at": bound_at,
        "updated_at": timestamp(),
    }
    write_registry(path, registry)
    emit({"action": "bind", "repo_root": str(root), "repo_key": repo_key, "binding": projects[repo_key]})


def command_get(args: argparse.Namespace, path: Path) -> None:
    root, repo_key = repository_identity(args.repo)
    registry = load_registry(path)
    emit({"repo_root": str(root), "repo_key": repo_key, "binding": require_entry(registry, repo_key)})


def command_list(_: argparse.Namespace, path: Path) -> None:
    registry = load_registry(path)
    emit({"registry": str(path), "projects": registry["projects"]})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    bind_parser = subparsers.add_parser("bind", help="Bind a GitHub repository to one ChatGPT conversation")
    bind_parser.add_argument("--repo", required=True)
    bind_parser.add_argument("--environment", required=True)
    bind_parser.add_argument("--conversation-url", required=True)
    bind_parser.add_argument("--conversation-title", required=True)
    bind_parser.add_argument("--model-label", default="Pro")
    bind_parser.add_argument("--replace", action="store_true")

    get_parser = subparsers.add_parser("get", help="Read one repository binding")
    get_parser.add_argument("--repo", required=True)

    subparsers.add_parser("list", help="List all local bindings")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    path = registry_path()
    try:
        if args.command == "bind":
            command_bind(args, path)
        elif args.command == "get":
            command_get(args, path)
        elif args.command == "list":
            command_list(args, path)
        else:
            parser.error(f"Unknown command: {args.command}")
    except RegistryError as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
