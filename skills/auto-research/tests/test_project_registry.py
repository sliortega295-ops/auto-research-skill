from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import stat
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_registry.py"
SPEC = importlib.util.spec_from_file_location("project_registry", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TEST_ROOT = Path("/tmp/lyy-experiments/auto-research/tests")


def message(index: int, role: str, text: str) -> dict:
    return {
        "index": index,
        "role": role,
        "message_id": f"m{index}",
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "links": [],
    }


class ProjectRegistryTests(unittest.TestCase):
    def setUp(self):
        TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="unit-", dir=TEST_ROOT)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin", "git@github.com:Owner/Repo.git"],
            check=True,
        )
        self.registry = self.root / "codex" / "auto-research" / "targets.json"
        self.url = "https://chatgpt.com/g/g-project/c/conversation-id"
        self.bind_args = Namespace(
            repo=str(self.repo),
            environment="env-one",
            conversation_url=self.url,
            conversation_title="Project review",
            model_label="Pro",
            replace=False,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def bind(self):
        with contextlib.redirect_stdout(io.StringIO()):
            MODULE.command_bind(self.bind_args, self.registry)

    def write_transcript(self, messages, *, url=None, environment="env-one") -> Path:
        path = self.root / "transcript.json"
        payload = {
            "schema_version": 1,
            "environment": environment,
            "tab": {"url": (url or self.url) + "?utm_source=test"},
            "message_count": len(messages),
            "messages": messages,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_canonical_github_remote(self):
        self.assertEqual(
            MODULE.canonical_github_remote("https://github.com/Owner/Repo.git"),
            "github.com/owner/repo",
        )
        self.assertEqual(
            MODULE.canonical_github_remote("ssh://git@github.com/Owner/Repo.git"),
            "github.com/owner/repo",
        )
        self.assertEqual(
            MODULE.canonical_github_remote("git@github.com:Owner/Repo.git"),
            "github.com/owner/repo",
        )
        for invalid in (
            "https://token@github.com/Owner/Repo.git",
            "token@github.com:Owner/Repo.git",
            "https://github.example/Owner/Repo.git",
            "file://github.com/Owner/Repo.git",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(MODULE.RegistryError):
                MODULE.canonical_github_remote(invalid)

    def test_bind_is_private_and_idempotent(self):
        self.bind()
        self.bind()
        registry = json.loads(self.registry.read_text(encoding="utf-8"))
        entry = registry["projects"]["github.com/owner/repo"]
        self.assertEqual(entry["conversation_url"], self.url)
        self.assertEqual(entry["model_label"], "Pro")
        self.assertEqual(stat.S_IMODE(self.registry.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.registry.parent.stat().st_mode), 0o700)

    def test_pending_and_mark_archived_verify_incremental_suffix(self):
        self.bind()
        transcript = self.write_transcript(
            [message(0, "user", "existing"), message(1, "assistant", "old reply")]
        )
        mark_args = Namespace(repo=str(self.repo), transcript=str(transcript))
        with contextlib.redirect_stdout(io.StringIO()):
            MODULE.command_mark_archived(mark_args, self.registry)

        transcript = self.write_transcript(
            [
                message(0, "user", "existing"),
                message(1, "assistant", "old reply"),
                message(2, "user", "checkpoint"),
                message(3, "assistant", "new review"),
            ]
        )
        pending_args = Namespace(repo=str(self.repo), transcript=str(transcript))
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            MODULE.command_pending(pending_args, self.registry)
        result = json.loads(stream.getvalue())
        self.assertEqual(result["baseline_message_count"], 2)
        self.assertEqual(result["pending_message_count"], 2)
        self.assertEqual([item["index"] for item in result["pending"]], [2, 3])

    def test_history_change_before_marker_fails_closed(self):
        self.bind()
        transcript = self.write_transcript(
            [message(0, "user", "original"), message(1, "assistant", "unchanged tail")]
        )
        args = Namespace(repo=str(self.repo), transcript=str(transcript))
        with contextlib.redirect_stdout(io.StringIO()):
            MODULE.command_mark_archived(args, self.registry)
        altered = self.write_transcript(
            [
                message(0, "user", "edited"),
                message(1, "assistant", "unchanged tail"),
                message(2, "user", "later"),
            ]
        )
        with self.assertRaisesRegex(MODULE.RegistryError, "history changed"):
            MODULE.command_pending(Namespace(repo=str(self.repo), transcript=str(altered)), self.registry)

    def test_wrong_conversation_or_environment_fails_closed(self):
        self.bind()
        wrong_url = self.write_transcript(
            [message(0, "user", "text")], url="https://chatgpt.com/c/another"
        )
        with self.assertRaisesRegex(MODULE.RegistryError, "different ChatGPT conversation"):
            MODULE.command_pending(
                Namespace(repo=str(self.repo), transcript=str(wrong_url)), self.registry
            )
        wrong_environment = self.write_transcript(
            [message(0, "user", "text")], environment="env-two"
        )
        with self.assertRaisesRegex(MODULE.RegistryError, "different AdsPower environment"):
            MODULE.command_pending(
                Namespace(repo=str(self.repo), transcript=str(wrong_environment)), self.registry
            )

    def test_replacing_conversation_resets_archive_marker(self):
        self.bind()
        transcript = self.write_transcript([message(0, "user", "baseline")])
        with contextlib.redirect_stdout(io.StringIO()):
            MODULE.command_mark_archived(
                Namespace(repo=str(self.repo), transcript=str(transcript)), self.registry
            )
        replacement = Namespace(
            **{
                **vars(self.bind_args),
                "conversation_url": "https://chatgpt.com/c/replacement",
                "replace": True,
            }
        )
        with contextlib.redirect_stdout(io.StringIO()):
            MODULE.command_bind(replacement, self.registry)
        entry = MODULE.load_registry(self.registry)["projects"]["github.com/owner/repo"]
        self.assertEqual(entry["last_archived_message_count"], 0)
        self.assertIsNone(entry["last_archived_message_sha256"])
        self.assertIsNone(entry["last_archived_prefix_sha256"])

    def test_one_conversation_cannot_bind_two_repositories(self):
        self.bind()
        other_repo = self.root / "other-repo"
        subprocess.run(["git", "init", "-q", str(other_repo)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(other_repo),
                "remote",
                "add",
                "origin",
                "https://github.com/Owner/Other.git",
            ],
            check=True,
        )
        other_args = Namespace(**{**vars(self.bind_args), "repo": str(other_repo)})
        with self.assertRaisesRegex(MODULE.RegistryError, "already bound"):
            MODULE.command_bind(other_args, self.registry)


if __name__ == "__main__":
    unittest.main()
