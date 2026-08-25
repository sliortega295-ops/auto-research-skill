from __future__ import annotations

import contextlib
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

    def test_rebinding_removes_legacy_archive_fields(self):
        self.bind()
        registry = MODULE.load_registry(self.registry)
        entry = registry["projects"]["github.com/owner/repo"]
        entry["last_archived_message_count"] = 4
        entry["last_archived_message_sha256"] = "a" * 64
        entry["last_archived_prefix_sha256"] = "b" * 64
        MODULE.write_registry(self.registry, registry)
        self.bind()
        entry = MODULE.load_registry(self.registry)["projects"]["github.com/owner/repo"]
        self.assertNotIn("last_archived_message_count", entry)
        self.assertNotIn("last_archived_message_sha256", entry)
        self.assertNotIn("last_archived_prefix_sha256", entry)

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
