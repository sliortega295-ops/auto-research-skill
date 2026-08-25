from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "adspower_chatgpt.py"
SPEC = importlib.util.spec_from_file_location("adspower_chatgpt", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeCDP:
    def __init__(self, evaluations, call_results=None):
        self.evaluations = list(evaluations)
        self.call_results = list(call_results or [])
        self.calls = []
        self.closed = False

    def evaluate(self, expression, await_promise=False, timeout=None):
        if not self.evaluations:
            raise AssertionError("Unexpected evaluate call")
        expected, value = self.evaluations.pop(0)
        if expected is not None:
            self.assert_expression(expression, expected)
        return value

    @staticmethod
    def assert_expression(expression, expected):
        if expression != expected:
            raise AssertionError("Unexpected JavaScript expression")

    def call(self, method, params=None):
        self.calls.append((method, params))
        if self.call_results:
            return self.call_results.pop(0)
        return {}

    def close(self):
        self.closed = True


class AdsPowerChatGPTTests(unittest.TestCase):
    def test_canonical_conversation_url(self):
        value = MODULE.canonical_conversation_url(
            "https://chatgpt.com/g/g-project/c/abc123/?utm_source=x#fragment"
        )
        self.assertEqual(value, "https://chatgpt.com/g/g-project/c/abc123")
        for invalid in (
            "https://example.com/c/abc",
            "https://user:secret@chatgpt.com/c/abc",
            "https://chatgpt.com:8443/c/abc",
            "https://chatgpt.com/",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(MODULE.SkillError):
                MODULE.canonical_conversation_url(invalid)

    def test_choose_tab_uses_canonical_exact_url(self):
        tabs = [
            {
                "id": "one",
                "title": "Project",
                "url": "https://chatgpt.com/c/first",
                "webSocketDebuggerUrl": "ws://127.0.0.1/one",
            },
            {
                "id": "two",
                "title": "Project",
                "url": "https://chatgpt.com/g/g-project/c/second?temporary-chat=true",
                "webSocketDebuggerUrl": "ws://127.0.0.1/two",
            },
        ]
        with mock.patch.object(MODULE, "list_tabs", return_value=tabs):
            selected = MODULE.choose_tab(
                {"cdp_port": 1},
                None,
                None,
                "https://chatgpt.com/g/g-project/c/second#latest",
            )
        self.assertEqual(selected["id"], "two")

    def test_canonical_project_url(self):
        self.assertEqual(
            MODULE.canonical_project_url(
                "https://chatgpt.com/g/g-p-project123/project/?utm_source=test"
            ),
            "https://chatgpt.com/g/g-p-project123/project",
        )
        for invalid in (
            "https://example.com/g/g-p-project123/project",
            "https://chatgpt.com/c/conversation",
            "https://chatgpt.com/g/g-p-project123/c/conversation",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(MODULE.SkillError):
                MODULE.canonical_project_url(invalid)

    def test_project_link_candidates_are_exact_and_deduplicated(self):
        raw = [
            {
                "label": " auto   research ",
                "href": "https://chatgpt.com/g/g-p-project123/project?source=sidebar",
            },
            {
                "label": "auto research",
                "href": "https://chatgpt.com/g/g-p-project123/project",
            },
            {"label": "not a project", "href": "https://example.com/project"},
        ]
        cdp = FakeCDP([(MODULE.PROJECT_LINKS_JS, raw)])
        self.assertEqual(
            MODULE.project_link_candidates(cdp),
            [
                {
                    "label": "auto research",
                    "url": "https://chatgpt.com/g/g-p-project123/project",
                }
            ],
        )

    def test_create_background_target_never_activates_it(self):
        environment = {"cdp_port": 1234}
        browser = FakeCDP([], call_results=[{"targetId": "new-tab"}])
        created = {
            "id": "new-tab",
            "title": "ChatGPT",
            "url": "https://chatgpt.com/g/g-p-project123/project",
            "webSocketDebuggerUrl": "ws://127.0.0.1/new-tab",
        }
        with (
            mock.patch.object(
                MODULE,
                "http_json",
                return_value={"webSocketDebuggerUrl": "ws://127.0.0.1/browser"},
            ),
            mock.patch.object(MODULE, "CDP", return_value=browser),
            mock.patch.object(MODULE, "list_tabs", return_value=[created]),
        ):
            result = MODULE.create_background_target(
                environment, "https://chatgpt.com/g/g-p-project123/project"
            )
        self.assertEqual(result["id"], "new-tab")
        self.assertEqual(
            browser.calls,
            [
                (
                    "Target.createTarget",
                    {
                        "url": "https://chatgpt.com/g/g-p-project123/project",
                        "background": True,
                    },
                )
            ],
        )
        self.assertTrue(browser.closed)

    def test_export_preserves_messages_and_hashes(self):
        raw = {
            "messages": [
                {"role": "user", "message_id": "u1", "text": "same", "links": []},
                {"role": "assistant", "message_id": "a1", "text": "same", "links": []},
            ],
            "top_stable": True,
            "scroll_restored_to": 42,
            "scroll_original_top": 42,
            "scroll_restored": True,
            "reached_bottom": True,
            "missing_message_ids": 0,
            "scroll_passes": 3,
            "scroll_client_height": 800,
            "scroll_height": 2400,
        }
        cdp = FakeCDP([(MODULE.EXPORT_CONVERSATION_JS, raw)])
        result = MODULE.export_conversation(cdp)
        self.assertEqual(result["message_count"], 2)
        self.assertEqual([item["index"] for item in result["messages"]], [0, 1])
        self.assertEqual(result["messages"][0]["sha256"], result["messages"][1]["sha256"])
        self.assertEqual(result["scroll_restored_to"], 42)
        self.assertTrue(result["scroll_restored"])
        self.assertEqual(result["scroll_passes"], 3)

    def test_export_fails_closed_when_traversal_is_incomplete(self):
        raw = {
            "messages": [],
            "top_stable": True,
            "reached_bottom": False,
            "missing_message_ids": 0,
        }
        cdp = FakeCDP([(MODULE.EXPORT_CONVERSATION_JS, raw)])
        with self.assertRaisesRegex(MODULE.SkillError, "complete rendered history"):
            MODULE.export_conversation(cdp)

    def test_select_model_is_verified_noop_when_already_selected(self):
        current = {"present": True, "label": " Pro ", "expanded": "false"}
        cdp = FakeCDP([(MODULE.MODEL_STATE_JS, current)])
        before, after = MODULE.select_model(cdp, "Pro")
        self.assertEqual(before, after)
        self.assertEqual(cdp.evaluations, [])
        self.assertEqual(cdp.calls, [])

    def test_select_model_opens_exact_option_and_verifies(self):
        cdp = FakeCDP(
            [
                (MODULE.MODEL_STATE_JS, {"present": True, "label": "Auto"}),
                (MODULE.OPEN_MODEL_MENU_JS, {"ok": True, "label": "Auto"}),
                (None, {"ok": True, "selected": "Pro"}),
                (MODULE.MODEL_STATE_JS, {"present": True, "label": "Pro"}),
            ]
        )
        before, after = MODULE.select_model(cdp, "Pro")
        self.assertEqual(before["label"], "Auto")
        self.assertEqual(after["label"], "Pro")

    def test_private_export_writer_is_mode_0600(self):
        MODULE.DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="unit-", dir=MODULE.DEFAULT_ROOT) as directory:
            output = Path(directory) / "conversation.json"
            MODULE.write_private_json(output, {"ok": True})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"ok": True})
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)

    def test_scratch_output_rejects_outside_path(self):
        with self.assertRaises(MODULE.SkillError):
            MODULE.scratch_output_path("/tmp/not-adspower/transcript.json")

    def test_wait_requires_new_assistant_message_and_idle(self):
        cdp = FakeCDP([])
        states = [
            {"generating": False, "assistant_message_count": 2},
            {"generating": True, "assistant_message_count": 3},
            {"generating": False, "assistant_message_count": 3},
        ]
        args = type(
            "Args",
            (),
            {"timeout": 1.0, "interval": 0.001, "after_assistant_count": 2},
        )()
        with (
            mock.patch.object(
                MODULE,
                "open_selected",
                return_value=(
                    {"environment": "env"},
                    {"id": "tab", "title": "Project", "url": "https://chatgpt.com/c/id"},
                    cdp,
                ),
            ),
            mock.patch.object(MODULE, "inspect", side_effect=states),
            mock.patch.object(MODULE.time, "sleep", return_value=None),
            contextlib.redirect_stdout(io.StringIO()) as stream,
        ):
            MODULE.command_wait(args)
        output = json.loads(stream.getvalue())
        self.assertEqual(output["state"]["assistant_message_count"], 3)
        self.assertFalse(output["state"]["generating"])
        self.assertTrue(cdp.closed)

    def test_wait_has_no_deadline_when_timeout_is_omitted(self):
        cdp = FakeCDP([])
        states = [
            {"generating": True, "assistant_message_count": 2},
            {"generating": False, "assistant_message_count": 3},
        ]
        args = type(
            "Args",
            (),
            {"timeout": None, "interval": 0.001, "after_assistant_count": 2},
        )()
        with (
            mock.patch.object(
                MODULE,
                "open_selected",
                return_value=(
                    {"environment": "env"},
                    {"id": "tab", "title": "Project", "url": "https://chatgpt.com/c/id"},
                    cdp,
                ),
            ),
            mock.patch.object(MODULE, "inspect", side_effect=states),
            mock.patch.object(MODULE.time, "sleep", return_value=None),
            mock.patch.object(
                MODULE.time,
                "monotonic",
                side_effect=AssertionError("an unlimited wait must not compute a deadline"),
            ),
            contextlib.redirect_stdout(io.StringIO()) as stream,
        ):
            MODULE.command_wait(args)
        output = json.loads(stream.getvalue())
        self.assertEqual(output["state"]["assistant_message_count"], 3)
        self.assertFalse(output["state"]["generating"])
        self.assertTrue(cdp.closed)


if __name__ == "__main__":
    unittest.main()
