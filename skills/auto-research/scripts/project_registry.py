#!/usr/bin/env python3
"""Maintain local GitHub-repository to ChatGPT-conversation bindings."""

from __future__ import annotations

import argparse
import hashlib
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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
        if existing.get("conversation_url") == conversation_url:
            archive_count = existing.get("last_archived_message_count", 0)
            archive_sha = existing.get("last_archived_message_sha256")
            archive_prefix_sha = existing.get("last_archived_prefix_sha256")
            bound_at = existing.get("bound_at") or timestamp()
        else:
            archive_count = 0
            archive_sha = None
            archive_prefix_sha = None
            bound_at = timestamp()
    else:
        archive_count = 0
        archive_sha = None
        archive_prefix_sha = None
        bound_at = timestamp()
    projects[repo_key] = {
        **desired_identity,
        "last_archived_message_count": archive_count,
        "last_archived_message_sha256": archive_sha,
        "last_archived_prefix_sha256": archive_prefix_sha,
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


def load_bound_transcript(
    args: argparse.Namespace,
    entry: dict[str, Any],
) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    transcript_path = Path(args.transcript).expanduser().resolve()
    try:
        transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Could not read transcript export: {exc}") from exc
    if not isinstance(transcript, dict):
        raise RegistryError("Transcript export must be a JSON object")
    messages = transcript.get("messages")
    if not isinstance(messages, list) or any(not isinstance(item, dict) for item in messages):
        raise RegistryError("Transcript export does not contain a valid messages list")
    if transcript.get("message_count") != len(messages):
        raise RegistryError("Transcript message count does not match its messages list")
    tab = transcript.get("tab")
    exported_url = tab.get("url") if isinstance(tab, dict) else None
    if not isinstance(exported_url, str):
        raise RegistryError("Transcript export does not identify its ChatGPT conversation URL")
    try:
        exported_url = canonical_conversation_url(exported_url)
    except RegistryError as exc:
        raise RegistryError(f"Transcript conversation URL is invalid: {exc}") from exc
    if exported_url != entry.get("conversation_url"):
        raise RegistryError("Transcript export came from a different ChatGPT conversation")
    if transcript.get("environment") != entry.get("environment"):
        raise RegistryError("Transcript export came from a different AdsPower environment")
    for expected_index, message in enumerate(messages):
        if message.get("index") != expected_index:
            raise RegistryError("Transcript message indexes are not contiguous")
        text = message.get("text")
        sha = message.get("sha256")
        if message.get("role") not in {"user", "assistant"}:
            raise RegistryError("Transcript message role is invalid")
        if (
            not isinstance(text, str)
            or not isinstance(sha, str)
            or not SHA256_RE.fullmatch(sha)
        ):
            raise RegistryError("Transcript message text or SHA-256 is invalid")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != sha:
            raise RegistryError("Transcript message SHA-256 verification failed")
    return transcript_path, transcript, messages


def prefix_sha256(messages: list[dict[str, Any]], count: int) -> str | None:
    if count == 0:
        return None
    material = json.dumps(
        [
            {"index": item["index"], "role": item["role"], "sha256": item["sha256"]}
            for item in messages[:count]
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def verify_archive_marker(entry: dict[str, Any], messages: list[dict[str, Any]]) -> int:
    count = entry.get("last_archived_message_count", 0)
    marker = entry.get("last_archived_message_sha256")
    prefix_marker = entry.get("last_archived_prefix_sha256")
    if not isinstance(count, int) or count < 0 or count > len(messages):
        raise RegistryError("Stored message count is incompatible with the current conversation")
    if count == 0:
        if marker is not None or prefix_marker is not None:
            raise RegistryError("Stored zero-message marker is inconsistent")
        return 0
    if not isinstance(marker, str) or not SHA256_RE.fullmatch(marker):
        raise RegistryError("Stored archive marker is invalid")
    if messages[count - 1].get("sha256") != marker:
        raise RegistryError(
            "Conversation history changed before the archive marker; resynchronize explicitly"
        )
    if prefix_marker is not None:
        if not isinstance(prefix_marker, str) or not SHA256_RE.fullmatch(prefix_marker):
            raise RegistryError("Stored archive prefix marker is invalid")
        if prefix_sha256(messages, count) != prefix_marker:
            raise RegistryError(
                "Conversation history changed before the archive marker; resynchronize explicitly"
            )
    return count


def command_mark_archived(args: argparse.Namespace, path: Path) -> None:
    root, repo_key = repository_identity(args.repo)
    registry = load_registry(path)
    entry = require_entry(registry, repo_key)
    transcript_path, _, messages = load_bound_transcript(args, entry)
    previous_count = verify_archive_marker(entry, messages)
    entry["last_archived_message_count"] = len(messages)
    entry["last_archived_message_sha256"] = messages[-1]["sha256"] if messages else None
    entry["last_archived_prefix_sha256"] = prefix_sha256(messages, len(messages))
    entry["updated_at"] = timestamp()
    write_registry(path, registry)
    emit(
        {
            "action": "mark-archived",
            "repo_root": str(root),
            "repo_key": repo_key,
            "transcript": str(transcript_path),
            "previous_message_count": previous_count,
            "binding": entry,
        }
    )


def command_pending(args: argparse.Namespace, path: Path) -> None:
    root, repo_key = repository_identity(args.repo)
    registry = load_registry(path)
    entry = require_entry(registry, repo_key)
    transcript_path, _, messages = load_bound_transcript(args, entry)
    start = verify_archive_marker(entry, messages)
    pending = messages[start:]
    emit(
        {
            "repo_root": str(root),
            "repo_key": repo_key,
            "transcript": str(transcript_path),
            "baseline_message_count": start,
            "current_message_count": len(messages),
            "pending_message_count": len(pending),
            "pending": [
                {
                    "index": item.get("index"),
                    "role": item.get("role"),
                    "sha256": item.get("sha256"),
                    "characters": len(item.get("text", "")),
                }
                for item in pending
            ],
            "latest_message_sha256": (
                messages[-1].get("sha256") if messages and isinstance(messages[-1], dict) else None
            ),
        }
    )


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

    mark_parser = subparsers.add_parser("mark-archived", help="Advance a repository transcript marker")
    mark_parser.add_argument("--repo", required=True)
    mark_parser.add_argument("--transcript", required=True)

    pending_parser = subparsers.add_parser("pending", help="Verify a transcript and summarize new messages")
    pending_parser.add_argument("--repo", required=True)
    pending_parser.add_argument("--transcript", required=True)
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
        elif args.command == "mark-archived":
            command_mark_archived(args, path)
        elif args.command == "pending":
            command_pending(args, path)
        else:
            parser.error(f"Unknown command: {args.command}")
    except RegistryError as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
