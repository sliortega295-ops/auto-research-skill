#!/usr/bin/env python3
"""Inspect and operate an existing ChatGPT tab in AdsPower/SunBrowser via CDP.

This helper deliberately does not expose browser cookies, local storage, saved
passwords, proxy credentials, or AdsPower fingerprint settings.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import socket
import struct
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_ROOT = Path("/tmp/lyy-experiments/adspower-chatgpt")


class SkillError(RuntimeError):
    pass


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def proc_cmdline_text(pid_dir: Path) -> str:
    try:
        raw = (pid_dir / "cmdline").read_bytes()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return ""
    # AdsPower can replace the normal NUL-separated argv with one protected
    # command-line string, so discovery must not depend on argv boundaries.
    return raw.replace(b"\0", b" ").decode("utf-8", "replace")


def discover_environments() -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        cmdline = proc_cmdline_text(pid_dir)
        if not cmdline:
            continue
        try:
            process_name = (pid_dir / "comm").read_text(encoding="utf-8").strip().lower()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "sunbrowser" not in process_name:
            continue
        if "--type=" in cmdline:
            continue
        match = re.search(r"--user-data-dir=(?:\"([^\"]+)\"|'([^']+)'|([^\s]+))", cmdline)
        user_data = next((group for group in match.groups() if group), None) if match else None
        if not user_data or "adspower" not in user_data.lower():
            continue
        profile_dir = Path(user_data)
        port_file = profile_dir / "DevToolsActivePort"
        try:
            lines = port_file.read_text(encoding="utf-8").splitlines()
            port = int(lines[0])
        except (FileNotFoundError, PermissionError, ValueError, IndexError):
            continue
        profile_name = profile_dir.name
        environment = profile_name.split("_", 1)[0]
        found.append(
            {
                "environment": environment,
                "pid": int(pid_dir.name),
                "profile_dir": str(profile_dir),
                "cdp_port": port,
            }
        )
    return sorted(found, key=lambda item: (item["environment"], item["pid"]))


def select_environment(name: str | None) -> dict[str, Any]:
    environments = discover_environments()
    if name:
        environments = [item for item in environments if item["environment"] == name]
    if not environments:
        suffix = f" named {name!r}" if name else ""
        raise SkillError(f"No live AdsPower/SunBrowser environment{suffix} with CDP enabled was found")
    if len(environments) > 1:
        raise SkillError(
            "Multiple AdsPower environments match; pass --environment. Candidates: "
            + ", ".join(f"{item['environment']} (pid {item['pid']})" for item in environments)
        )
    return environments[0]


def http_json(url: str) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            return json.load(response)
    except Exception as exc:
        raise SkillError(f"CDP endpoint is unavailable: {exc}") from exc


def is_chatgpt_url(url: str) -> bool:
    try:
        host = (urllib.parse.urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host == "chatgpt.com" or host.endswith(".chatgpt.com")


def canonical_conversation_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise SkillError(f"Invalid ChatGPT conversation URL: {exc}") from exc
    if parsed.scheme not in {"http", "https"} or not is_chatgpt_url(url):
        raise SkillError("Conversation URL must use http(s) on chatgpt.com")
    if parsed.username or parsed.password:
        raise SkillError("Conversation URL must not contain credentials")
    if port not in {None, 80, 443}:
        raise SkillError("Conversation URL must not use a custom port")
    path = re.sub(r"/+$", "", parsed.path or "") or "/"
    if "/c/" not in path:
        raise SkillError("Conversation URL must identify a ChatGPT /c/ conversation")
    return urllib.parse.urlunsplit(("https", host, path, "", ""))


def maybe_canonical_conversation_url(url: str) -> str | None:
    try:
        return canonical_conversation_url(url)
    except SkillError:
        return None


def canonical_project_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise SkillError(f"Invalid ChatGPT project URL: {exc}") from exc
    if parsed.scheme not in {"http", "https"} or not is_chatgpt_url(url):
        raise SkillError("Project URL must use http(s) on chatgpt.com")
    if parsed.username or parsed.password:
        raise SkillError("Project URL must not contain credentials")
    if port not in {None, 80, 443}:
        raise SkillError("Project URL must not use a custom port")
    path = re.sub(r"/+$", "", parsed.path or "")
    if not re.fullmatch(r"/g/g-p-[^/]+(?:/project)?", path):
        raise SkillError("Project URL must identify a ChatGPT project page")
    return urllib.parse.urlunsplit(("https", host, path, "", ""))


def list_tabs(environment: dict[str, Any]) -> list[dict[str, Any]]:
    targets = http_json(f"http://127.0.0.1:{environment['cdp_port']}/json/list")
    tabs: list[dict[str, Any]] = []
    for target in targets:
        if target.get("type") != "page" or not is_chatgpt_url(target.get("url", "")):
            continue
        tabs.append(
            {
                "id": target.get("id"),
                "title": target.get("title", ""),
                "url": target.get("url", ""),
                "webSocketDebuggerUrl": target.get("webSocketDebuggerUrl"),
            }
        )
    return tabs


class WebSocket:
    def __init__(self, url: str, timeout: float = 8.0):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "ws" or not parsed.hostname:
            raise SkillError(f"Unsupported CDP WebSocket URL: {url}")
        self.sock = socket.create_connection((parsed.hostname, parsed.port or 80), timeout=timeout)
        self.sock.settimeout(timeout)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port or 80}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = self._recv_headers()
        first_line, _, raw_headers = response.partition(b"\r\n")
        if b" 101 " not in first_line:
            raise SkillError(f"CDP WebSocket handshake failed: {first_line.decode('latin1', 'replace')}")
        headers: dict[bytes, bytes] = {}
        for line in raw_headers.split(b"\r\n"):
            if b":" in line:
                key_bytes, value = line.split(b":", 1)
                headers[key_bytes.strip().lower()] = value.strip()
        expected = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest())
        if headers.get(b"sec-websocket-accept") != expected:
            raise SkillError("CDP WebSocket handshake returned an invalid accept key")

    def _recv_headers(self) -> bytes:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise SkillError("CDP WebSocket closed during handshake")
            data.extend(chunk)
            if len(data) > 65536:
                raise SkillError("CDP WebSocket returned oversized handshake headers")
        return bytes(data)

    def _read_exact(self, length: int) -> bytes:
        data = bytearray()
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise SkillError("CDP WebSocket closed unexpectedly")
            data.extend(chunk)
        return bytes(data)

    def send_frame(self, opcode: int, payload: bytes) -> None:
        mask = secrets.token_bytes(4)
        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def send_json(self, value: Any) -> None:
        self.send_frame(0x1, json.dumps(value, separators=(",", ":")).encode("utf-8"))

    def recv_message(self) -> str:
        fragments = bytearray()
        message_opcode: int | None = None
        while True:
            first, second = self._read_exact(2)
            final = bool(first & 0x80)
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else b""
            payload = self._read_exact(length)
            if masked:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x8:
                raise SkillError("CDP WebSocket was closed")
            if opcode == 0x9:
                self.send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode in (0x1, 0x2):
                message_opcode = opcode
                fragments = bytearray(payload)
            elif opcode == 0x0 and message_opcode is not None:
                fragments.extend(payload)
            else:
                continue
            if final:
                if message_opcode != 0x1:
                    raise SkillError("CDP returned an unexpected binary WebSocket message")
                return fragments.decode("utf-8")

    def close(self) -> None:
        try:
            self.send_frame(0x8, b"")
        except Exception:
            pass
        self.sock.close()


class CDP:
    def __init__(self, websocket_url: str):
        self.websocket = WebSocket(websocket_url)
        self.next_id = 1

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        call_id = self.next_id
        self.next_id += 1
        message: dict[str, Any] = {"id": call_id, "method": method}
        if params is not None:
            message["params"] = params
        self.websocket.send_json(message)
        while True:
            try:
                response = json.loads(self.websocket.recv_message())
            except TimeoutError as exc:
                raise SkillError(f"CDP {method} timed out while waiting for the page") from exc
            if response.get("id") != call_id:
                continue
            if "error" in response:
                raise SkillError(f"CDP {method} failed: {response['error']}")
            return response.get("result", {})

    def evaluate(
        self,
        expression: str,
        await_promise: bool = False,
        timeout: float | None = None,
    ) -> Any:
        previous_timeout = self.websocket.sock.gettimeout()
        if timeout is not None:
            self.websocket.sock.settimeout(timeout)
        try:
            result = self.call(
                "Runtime.evaluate",
                {
                    "expression": expression,
                    "returnByValue": True,
                    "awaitPromise": await_promise,
                },
            ).get("result", {})
        finally:
            if timeout is not None:
                self.websocket.sock.settimeout(previous_timeout)
        if result.get("subtype") == "error":
            raise SkillError(result.get("description", "JavaScript evaluation failed"))
        return result.get("value")

    def close(self) -> None:
        self.websocket.close()


def tab_summary(tab: dict[str, Any]) -> dict[str, Any]:
    return {key: tab.get(key) for key in ("id", "title", "url")}


def choose_tab(
    environment: dict[str, Any],
    tab_id: str | None,
    tab_title: str | None,
    conversation_url: str | None = None,
) -> dict[str, Any]:
    tabs = list_tabs(environment)
    if tab_id:
        tabs = [tab for tab in tabs if tab.get("id") == tab_id]
    if tab_title:
        needle = tab_title.casefold()
        tabs = [tab for tab in tabs if needle in tab.get("title", "").casefold()]
    if conversation_url:
        target_url = canonical_conversation_url(conversation_url)
        tabs = [
            tab
            for tab in tabs
            if maybe_canonical_conversation_url(tab.get("url", "")) == target_url
        ]
    if not tabs:
        raise SkillError("No ChatGPT tab matched the requested selectors")
    if len(tabs) == 1:
        return tabs[0]
    visible: list[dict[str, Any]] = []
    for tab in tabs:
        websocket_url = tab.get("webSocketDebuggerUrl")
        if not websocket_url:
            continue
        cdp = CDP(websocket_url)
        try:
            if cdp.evaluate("document.visibilityState") == "visible":
                visible.append(tab)
        finally:
            cdp.close()
    if len(visible) == 1:
        return visible[0]
    raise SkillError(
        "Multiple ChatGPT tabs match; pass --conversation-url, --tab-id, or a unique "
        "--tab-title. Candidates: "
        + json.dumps([tab_summary(tab) for tab in tabs], ensure_ascii=False)
    )


INSPECT_JS = r"""
(() => {
  const isVisible = (el) => {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const text = (document.body?.innerText || '').replace(/\n{3,}/g, '\n\n');
  const userMessages = document.querySelectorAll('[data-message-author-role="user"]').length;
  const assistantMessages = document.querySelectorAll('[data-message-author-role="assistant"]').length;
  const editor = document.querySelector('#prompt-textarea, textarea[data-testid="prompt-textarea"], div.ProseMirror[contenteditable="true"]');
  const stop = document.querySelector('[data-testid="stop-button"], button[aria-label*="Stop generating" i]');
  const send = document.querySelector('[data-testid="send-button"], button[aria-label*="Send" i]');
  const directLabel = [...document.querySelectorAll('.uFxlGa_SliderTriggerChatSelectionLabel')].find(isVisible);
  let modelLabel = (directLabel?.innerText || '').trim() || null;
  if (!modelLabel && editor) {
    const editorRect = editor.getBoundingClientRect();
    const candidates = [...document.querySelectorAll('button[aria-haspopup="menu"]')]
      .filter(isVisible)
      .map((button) => {
        const rect = button.getBoundingClientRect();
        return {
          text: (button.innerText || '').trim(),
          distance: Math.abs((rect.top + rect.height / 2) - (editorRect.top + editorRect.height / 2)),
        };
      })
      .filter((item) => item.text && item.text.length <= 60 && item.distance < 140)
      .sort((a, b) => a.distance - b.distance);
    modelLabel = candidates[0]?.text || null;
  }
  return {
    title: document.title,
    url: location.href,
    visibility: document.visibilityState,
    editor_present: Boolean(editor),
    generating: Boolean(stop),
    send_enabled: Boolean(send && !send.disabled && send.getAttribute('aria-disabled') !== 'true'),
    model_label: modelLabel,
    user_message_count: userMessages,
    assistant_message_count: assistantMessages,
    body_excerpt: text.slice(-6000)
  };
})()
"""


PROJECT_LINKS_JS = r"""
(() => {
  const normalize = (value) => (value || '').trim().replace(/\s+/g, ' ');
  const found = [];
  for (const element of document.querySelectorAll('a[href]')) {
    const href = element.href || '';
    if (!/\/g\/g-p-[^/]+(?:\/project)?(?:[?#]|$)/.test(href)) continue;
    const raw = element.innerText || element.getAttribute('aria-label') || '';
    const firstLine = raw.split(/\n/).map((line) => normalize(line)).find(Boolean) || '';
    if (firstLine) found.push({label: firstLine, href});
  }
  return found;
})()
"""


MODEL_STATE_JS = r"""
(() => {
  const isVisible = (el) => {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const editor = document.querySelector('#prompt-textarea, textarea[data-testid="prompt-textarea"], div.ProseMirror[contenteditable="true"]');
  const directLabel = [...document.querySelectorAll('.uFxlGa_SliderTriggerChatSelectionLabel')].find(isVisible);
  let trigger = directLabel?.closest('button[aria-haspopup="menu"]') || null;
  if (!trigger && editor) {
    const editorRect = editor.getBoundingClientRect();
    const candidates = [...document.querySelectorAll('button[aria-haspopup="menu"]')]
      .filter(isVisible)
      .map((button) => {
        const rect = button.getBoundingClientRect();
        return {
          button,
          text: (button.innerText || '').trim(),
          distance: Math.abs((rect.top + rect.height / 2) - (editorRect.top + editorRect.height / 2)),
        };
      })
      .filter((item) => item.text && item.text.length <= 60 && item.distance < 140)
      .sort((a, b) => a.distance - b.distance);
    trigger = candidates[0]?.button || null;
  }
  return {
    present: Boolean(trigger),
    label: (directLabel?.innerText || trigger?.innerText || '').trim() || null,
    expanded: trigger?.getAttribute('aria-expanded') || null,
  };
})()
"""


OPEN_MODEL_MENU_JS = r"""
(() => {
  const isVisible = (el) => {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const editor = document.querySelector('#prompt-textarea, textarea[data-testid="prompt-textarea"], div.ProseMirror[contenteditable="true"]');
  const directLabel = [...document.querySelectorAll('.uFxlGa_SliderTriggerChatSelectionLabel')].find(isVisible);
  let trigger = directLabel?.closest('button[aria-haspopup="menu"]') || null;
  if (!trigger && editor) {
    const editorRect = editor.getBoundingClientRect();
    const candidates = [...document.querySelectorAll('button[aria-haspopup="menu"]')]
      .filter(isVisible)
      .map((button) => {
        const rect = button.getBoundingClientRect();
        return {
          button,
          text: (button.innerText || '').trim(),
          distance: Math.abs((rect.top + rect.height / 2) - (editorRect.top + editorRect.height / 2)),
        };
      })
      .filter((item) => item.text && item.text.length <= 60 && item.distance < 140)
      .sort((a, b) => a.distance - b.distance);
    trigger = candidates[0]?.button || null;
  }
  if (!trigger) return {ok: false, reason: 'composer model control not found'};
  if (trigger.getAttribute('aria-expanded') !== 'true') trigger.click();
  return {ok: true, label: (directLabel?.innerText || trigger.innerText || '').trim() || null};
})()
"""


EXPORT_CONVERSATION_JS = r"""
(async () => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const messageSelector = '[data-message-author-role]';
  const seed = document.querySelector(messageSelector);
  let scroller = document.scrollingElement || document.documentElement;
  for (let node = seed?.parentElement; node; node = node.parentElement) {
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    if (
      node.clientHeight >= 200 &&
      rect.height >= 200 &&
      node.scrollHeight > node.clientHeight + 4 &&
      /(auto|scroll)/.test(style.overflowY)
    ) {
      scroller = node;
      break;
    }
  }
  const originalTop = scroller.scrollTop;
  const originalScrollBehavior = scroller.style.scrollBehavior;
  scroller.style.scrollBehavior = 'auto';
  const collected = new Map();
  let missingMessageIds = 0;
  const collect = () => {
    for (const el of document.querySelectorAll(messageSelector)) {
      const role = el.getAttribute('data-message-author-role') || 'unknown';
      if (role !== 'user' && role !== 'assistant') continue;
      const text = el.innerText || '';
      const messageId = el.getAttribute('data-message-id') || el.closest('[data-message-id]')?.getAttribute('data-message-id') || null;
      if (!messageId) missingMessageIds += 1;
      const key = messageId ? `id:${messageId}` : `content:${role}:${text}`;
      if (collected.has(key)) continue;
      const links = [...el.querySelectorAll('a[href]')].map((anchor) => ({
        text: (anchor.innerText || '').trim(),
        href: anchor.href,
      }));
      collected.set(key, {role, message_id: messageId, text, links});
    }
  };
  let passes = 0;
  let reachedBottom = false;
  let topStable = false;
  let observedClientHeight = scroller.clientHeight;
  let observedScrollHeight = scroller.scrollHeight;
  let restoredTop = originalTop;
  try {
    let stableTopPasses = 0;
    let topAttempts = 0;
    let previousHeight = -1;
    let previousCount = -1;
    while (stableTopPasses < 2 && topAttempts++ < 20) {
      scroller.scrollTop = 0;
      await sleep(180);
      collect();
      const unchanged = scroller.scrollHeight === previousHeight && collected.size === previousCount;
      stableTopPasses = unchanged ? stableTopPasses + 1 : 0;
      previousHeight = scroller.scrollHeight;
      previousCount = collected.size;
    }
    topStable = stableTopPasses >= 2;
    while (passes++ < 1200) {
      collect();
      const bottom = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
      observedClientHeight = scroller.clientHeight;
      observedScrollHeight = scroller.scrollHeight;
      if (scroller.scrollTop >= bottom - 2) {
        reachedBottom = true;
        break;
      }
      const before = scroller.scrollTop;
      const step = Math.max(400, Math.floor(scroller.clientHeight * 0.8));
      scroller.scrollTop = Math.min(bottom, before + step);
      await sleep(40);
      if (scroller.scrollTop === before) {
        await sleep(80);
        if (scroller.scrollTop === before) break;
      }
    }
    collect();
  } finally {
    scroller.scrollTop = originalTop;
    await sleep(50);
    restoredTop = scroller.scrollTop;
    scroller.style.scrollBehavior = originalScrollBehavior;
  }
  return {
    messages: [...collected.values()],
    scroll_original_top: originalTop,
    scroll_restored_to: restoredTop,
    scroll_restored: Math.abs(restoredTop - originalTop) <= 2,
    top_stable: topStable,
    reached_bottom: reachedBottom,
    missing_message_ids: missingMessageIds,
    scroll_passes: passes,
    scroll_client_height: observedClientHeight,
    scroll_height: observedScrollHeight,
  };
})()
"""


def inspect(cdp: CDP) -> dict[str, Any]:
    result = cdp.evaluate(INSPECT_JS)
    if not isinstance(result, dict):
        raise SkillError("ChatGPT page inspection returned an unexpected result")
    return result


def project_link_candidates(cdp: CDP) -> list[dict[str, str]]:
    raw = cdp.evaluate(PROJECT_LINKS_JS)
    if not isinstance(raw, list):
        raise SkillError("ChatGPT project-link inspection returned an unexpected result")
    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = " ".join(str(item.get("label") or "").split())
        href = item.get("href")
        if not label or not isinstance(href, str):
            continue
        try:
            project_url = canonical_project_url(href)
        except SkillError:
            continue
        identity = (label.casefold(), project_url)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append({"label": label, "url": project_url})
    return candidates


def find_project_url(environment: dict[str, Any], project_name: str) -> tuple[str, list[str]]:
    normalized_name = " ".join(project_name.split()).casefold()
    if not normalized_name:
        raise SkillError("Project name is empty")
    matches: set[str] = set()
    available: set[str] = set()
    for tab in list_tabs(environment):
        websocket_url = tab.get("webSocketDebuggerUrl")
        if not websocket_url:
            continue
        cdp = CDP(websocket_url)
        try:
            candidates = project_link_candidates(cdp)
        finally:
            cdp.close()
        for candidate in candidates:
            available.add(candidate["label"])
            if candidate["label"].casefold() == normalized_name:
                matches.add(candidate["url"])
    if not matches:
        suffix = f" Available projects: {sorted(available)}" if available else ""
        raise SkillError(f"No exact ChatGPT project matched {project_name!r}.{suffix}")
    if len(matches) != 1:
        raise SkillError(
            f"Project name {project_name!r} resolved to multiple URLs: {sorted(matches)}"
        )
    return next(iter(matches)), sorted(available)


def create_background_target(environment: dict[str, Any], url: str) -> dict[str, Any]:
    version = http_json(f"http://127.0.0.1:{environment['cdp_port']}/json/version")
    websocket_url = version.get("webSocketDebuggerUrl") if isinstance(version, dict) else None
    if not websocket_url:
        raise SkillError("AdsPower browser target does not expose a browser-level CDP WebSocket")
    browser = CDP(websocket_url)
    try:
        result = browser.call("Target.createTarget", {"url": url, "background": True})
    finally:
        browser.close()
    target_id = result.get("targetId") if isinstance(result, dict) else None
    if not target_id:
        raise SkillError("CDP did not return a target ID for the background project tab")
    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        matching = [tab for tab in list_tabs(environment) if tab.get("id") == target_id]
        if len(matching) == 1:
            return matching[0]
        time.sleep(0.2)
    raise SkillError("The new background ChatGPT target did not become available")


def wait_for_editor(cdp: CDP, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    state = inspect(cdp)
    while not state.get("editor_present"):
        if time.monotonic() >= deadline:
            raise SkillError("The background ChatGPT project page did not become ready")
        time.sleep(0.25)
        state = inspect(cdp)
    return state


def normalize_label(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def model_state(cdp: CDP) -> dict[str, Any]:
    result = cdp.evaluate(MODEL_STATE_JS)
    if not isinstance(result, dict):
        raise SkillError("ChatGPT model control inspection returned an unexpected result")
    return result


def close_open_menu(cdp: CDP) -> None:
    for event_type in ("keyDown", "keyUp"):
        cdp.call(
            "Input.dispatchKeyEvent",
            {
                "type": event_type,
                "key": "Escape",
                "code": "Escape",
                "windowsVirtualKeyCode": 27,
                "nativeVirtualKeyCode": 27,
            },
        )


def select_model(cdp: CDP, target_label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    target_label = " ".join(target_label.split())
    if not target_label:
        raise SkillError("Target model label is empty")
    before = model_state(cdp)
    if not before.get("present"):
        raise SkillError("ChatGPT composer model control was not found")
    if normalize_label(before.get("label")) == normalize_label(target_label):
        return before, before

    opened = cdp.evaluate(OPEN_MODEL_MENU_JS)
    if not isinstance(opened, dict) or not opened.get("ok"):
        raise SkillError((opened or {}).get("reason", "Could not open the ChatGPT model menu"))

    deadline = time.monotonic() + 4.0
    result: dict[str, Any] | None = None
    target_json = json.dumps(target_label, ensure_ascii=False)
    select_expression = rf"""
(() => {{
  const target = {target_json};
  const normalize = (value) => (value || '').trim().replace(/\s+/g, ' ').toLocaleLowerCase();
  const isVisible = (el) => {{
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  }};
  const scopes = [...document.querySelectorAll('[role="menu"], [role="listbox"], [data-radix-menu-content], [data-state="open"]')]
    .filter(isVisible);
  const root = scopes.find((scope) => scope.querySelector('[role="menuitem"], [role="option"]')) || scopes.at(-1);
  if (!root) return {{ok: false, reason: 'model menu did not become visible', candidates: []}};
  const choices = [...root.querySelectorAll('[role="menuitem"], [role="option"], button')]
    .filter(isVisible)
    .map((el) => {{
      const raw = (el.innerText || el.getAttribute('aria-label') || '').trim();
      const firstLine = raw.split(/\n/).map((line) => line.trim()).find(Boolean) || '';
      return {{el, raw, firstLine}};
    }})
    .filter((item) => item.raw);
  const matches = choices.filter((item) => normalize(item.firstLine) === normalize(target));
  if (matches.length !== 1) {{
    return {{
      ok: false,
      reason: matches.length ? 'model label matched more than one visible option' : 'target model option not found',
      candidates: choices.map((item) => item.firstLine),
    }};
  }}
  matches[0].el.click();
  return {{ok: true, selected: matches[0].firstLine}};
}})()
"""
    while time.monotonic() < deadline:
        candidate = cdp.evaluate(select_expression)
        if isinstance(candidate, dict) and candidate.get("ok"):
            result = candidate
            break
        result = candidate if isinstance(candidate, dict) else None
        time.sleep(0.2)
    if not result or not result.get("ok"):
        close_open_menu(cdp)
        detail = result or {}
        candidates = detail.get("candidates") or []
        suffix = f"; visible candidates: {candidates}" if candidates else ""
        raise SkillError(detail.get("reason", "Could not select the target model") + suffix)

    verify_deadline = time.monotonic() + 6.0
    after = model_state(cdp)
    while normalize_label(after.get("label")) != normalize_label(target_label):
        if time.monotonic() >= verify_deadline:
            raise SkillError(
                f"Model selection did not verify: expected {target_label!r}, observed {after.get('label')!r}"
            )
        time.sleep(0.25)
        after = model_state(cdp)
    return before, after


def export_conversation(cdp: CDP) -> dict[str, Any]:
    raw = cdp.evaluate(EXPORT_CONVERSATION_JS, await_promise=True, timeout=90.0)
    if not isinstance(raw, dict) or not isinstance(raw.get("messages"), list):
        raise SkillError("ChatGPT conversation export returned an unexpected result")
    if not raw.get("top_stable"):
        raise SkillError("ChatGPT conversation export could not stabilize the oldest rendered history")
    if not raw.get("reached_bottom"):
        raise SkillError(
            "ChatGPT conversation export could not traverse the complete rendered history"
        )
    if raw.get("missing_message_ids"):
        raise SkillError("ChatGPT conversation export found messages without stable rendered IDs")
    messages: list[dict[str, Any]] = []
    for raw_message in raw["messages"]:
        if not isinstance(raw_message, dict):
            continue
        role = raw_message.get("role")
        if role not in {"user", "assistant"}:
            continue
        text_value = raw_message.get("text")
        if not isinstance(text_value, str):
            text_value = ""
        links: list[dict[str, str]] = []
        for raw_link in raw_message.get("links") or []:
            if not isinstance(raw_link, dict):
                continue
            href = raw_link.get("href")
            if not isinstance(href, str) or not href:
                continue
            links.append(
                {
                    "text": str(raw_link.get("text") or ""),
                    "href": href,
                }
            )
        messages.append(
            {
                "index": len(messages),
                "role": role,
                "message_id": raw_message.get("message_id"),
                "text": text_value,
                "sha256": hashlib.sha256(text_value.encode("utf-8")).hexdigest(),
                "links": links,
            }
        )
    transcript_material = json.dumps(
        [{"role": item["role"], "text": item["text"]} for item in messages],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "messages": messages,
        "message_count": len(messages),
        "user_message_count": sum(item["role"] == "user" for item in messages),
        "assistant_message_count": sum(item["role"] == "assistant" for item in messages),
        "total_characters": sum(len(item["text"]) for item in messages),
        "conversation_sha256": hashlib.sha256(transcript_material).hexdigest(),
        "scroll_original_top": raw.get("scroll_original_top"),
        "scroll_restored_to": raw.get("scroll_restored_to"),
        "scroll_restored": raw.get("scroll_restored"),
        "scroll_passes": raw.get("scroll_passes"),
        "scroll_client_height": raw.get("scroll_client_height"),
        "scroll_height": raw.get("scroll_height"),
    }


def scratch_output_path(path_value: str) -> Path:
    output = Path(path_value).expanduser().resolve()
    if DEFAULT_ROOT not in output.parents:
        raise SkillError(f"Output files must be stored under {DEFAULT_ROOT}")
    return output


def write_private_json(output: Path, value: Any) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_name = stream.name
            os.fchmod(stream.fileno(), 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, output)
        temporary_name = None
        output.chmod(0o600)
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def require_confirm(args: argparse.Namespace) -> None:
    if not getattr(args, "confirm", False):
        raise SkillError("Mutation blocked: repeat with --confirm only after the user explicitly requested it")


def require_idle(cdp: CDP) -> dict[str, Any]:
    before = inspect(cdp)
    if before.get("generating"):
        raise SkillError("ChatGPT is currently generating; wait for it to finish unless the user explicitly asks to stop it")
    return before


def read_prompt(path_value: str) -> str:
    if path_value == "-":
        value = sys.stdin.read()
    else:
        path = Path(path_value).expanduser().resolve()
        if DEFAULT_ROOT not in path.parents:
            raise SkillError(f"Prompt files must be stored under {DEFAULT_ROOT}")
        value = path.read_text(encoding="utf-8")
    if not value.strip():
        raise SkillError("Prompt text is empty")
    return value


def fill_editor(cdp: CDP, text_value: str) -> None:
    prepared = cdp.evaluate(
        r"""
(() => {
  const el = document.querySelector('#prompt-textarea, textarea[data-testid="prompt-textarea"], div.ProseMirror[contenteditable="true"]');
  if (!el) return {ok: false, reason: 'prompt editor not found'};
  el.focus();
  if (el instanceof HTMLTextAreaElement || el instanceof HTMLInputElement) {
    const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value')?.set;
    if (setter) setter.call(el, ''); else el.value = '';
  } else {
    el.replaceChildren();
  }
  el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'deleteContentBackward', data: null}));
  return {ok: true};
})()
"""
    )
    if not prepared or not prepared.get("ok"):
        raise SkillError((prepared or {}).get("reason", "Could not prepare the ChatGPT prompt editor"))
    cdp.call("Input.insertText", {"text": text_value})
    time.sleep(0.25)


def click_send(cdp: CDP) -> None:
    result = cdp.evaluate(
        r"""
(() => {
  if (document.querySelector('[data-testid="stop-button"], button[aria-label*="Stop generating" i]')) {
    return {ok: false, reason: 'generation is in progress'};
  }
  const button = document.querySelector('[data-testid="send-button"], button[aria-label*="Send" i]');
  if (!button) return {ok: false, reason: 'send button not found'};
  if (button.disabled || button.getAttribute('aria-disabled') === 'true') return {ok: false, reason: 'send button is disabled'};
  button.click();
  return {ok: true};
})()
"""
    )
    if not result or not result.get("ok"):
        raise SkillError((result or {}).get("reason", "Could not click the ChatGPT send button"))


def open_selected(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], CDP]:
    environment = select_environment(args.environment)
    tab = choose_tab(environment, args.tab_id, args.tab_title, args.conversation_url)
    websocket_url = tab.get("webSocketDebuggerUrl")
    if not websocket_url:
        raise SkillError("Selected ChatGPT tab does not expose a CDP WebSocket")
    return environment, tab, CDP(websocket_url)


def command_discover(_: argparse.Namespace) -> None:
    emit({"environments": discover_environments()})


def command_tabs(args: argparse.Namespace) -> None:
    environment = select_environment(args.environment)
    emit(
        {
            "environment": environment["environment"],
            "tabs": [tab_summary(tab) for tab in list_tabs(environment)],
        }
    )


def command_open_project(args: argparse.Namespace) -> None:
    require_confirm(args)
    environment = select_environment(args.environment)
    project_url, available = find_project_url(environment, args.project_name)
    tab = create_background_target(environment, project_url)
    websocket_url = tab.get("webSocketDebuggerUrl")
    if not websocket_url:
        raise SkillError("The new background ChatGPT tab does not expose a CDP WebSocket")
    cdp = CDP(websocket_url)
    try:
        state = wait_for_editor(cdp)
    finally:
        cdp.close()
    if state.get("visibility") == "visible":
        raise SkillError("The new project target unexpectedly became the visible browser tab")
    emit(
        {
            "action": "open-project",
            "environment": environment["environment"],
            "project_name": " ".join(args.project_name.split()),
            "project_url": project_url,
            "available_projects": available,
            "tab": tab_summary(tab),
            "state": state,
        }
    )


def command_inspect(args: argparse.Namespace) -> None:
    environment, tab, cdp = open_selected(args)
    try:
        state = inspect(cdp)
    finally:
        cdp.close()
    emit({"environment": environment["environment"], "tab": tab_summary(tab), "state": state})


def command_select_model(args: argparse.Namespace) -> None:
    require_confirm(args)
    environment, tab, cdp = open_selected(args)
    try:
        page_before = require_idle(cdp)
        model_before, model_after = select_model(cdp, args.name)
        page_after = inspect(cdp)
    finally:
        cdp.close()
    emit(
        {
            "action": "select-model",
            "environment": environment["environment"],
            "tab": tab_summary(tab),
            "changed": normalize_label(model_before.get("label"))
            != normalize_label(model_after.get("label")),
            "model_before": model_before,
            "model_after": model_after,
            "page_before": page_before,
            "page_after": page_after,
        }
    )


def command_export_conversation(args: argparse.Namespace) -> None:
    environment, tab, cdp = open_selected(args)
    try:
        state = inspect(cdp)
        transcript = export_conversation(cdp)
    finally:
        cdp.close()
    output = scratch_output_path(args.output)
    payload = {
        "schema_version": 1,
        "exported_at": datetime.now().astimezone().isoformat(),
        "environment": environment["environment"],
        "tab": tab_summary(tab),
        "state": {
            key: state.get(key)
            for key in (
                "title",
                "url",
                "visibility",
                "generating",
                "model_label",
                "user_message_count",
                "assistant_message_count",
            )
        },
        **transcript,
    }
    write_private_json(output, payload)
    emit(
        {
            "action": "export-conversation",
            "environment": environment["environment"],
            "tab": tab_summary(tab),
            "output": str(output),
            "generating": state.get("generating"),
            "model_label": state.get("model_label"),
            "message_count": transcript["message_count"],
            "user_message_count": transcript["user_message_count"],
            "assistant_message_count": transcript["assistant_message_count"],
            "total_characters": transcript["total_characters"],
            "conversation_sha256": transcript["conversation_sha256"],
            "scroll_passes": transcript["scroll_passes"],
            "scroll_restored": transcript["scroll_restored"],
            "scroll_client_height": transcript["scroll_client_height"],
            "scroll_height": transcript["scroll_height"],
            "last_message_sha256": (
                transcript["messages"][-1]["sha256"] if transcript["messages"] else None
            ),
        }
    )


def command_screenshot(args: argparse.Namespace) -> None:
    environment, tab, cdp = open_selected(args)
    if args.output:
        output = Path(args.output).expanduser().resolve()
    else:
        run_dir = DEFAULT_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S")
        output = run_dir / f"{environment['environment']}-chatgpt.png"
    if DEFAULT_ROOT not in output.parents:
        raise SkillError(f"Screenshots must be stored under {DEFAULT_ROOT}")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = cdp.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
    finally:
        cdp.close()
    data = result.get("data")
    if not data:
        raise SkillError("CDP did not return screenshot data")
    output.write_bytes(base64.b64decode(data))
    emit({"environment": environment["environment"], "tab": tab_summary(tab), "screenshot": str(output)})


def command_new_chat(args: argparse.Namespace) -> None:
    require_confirm(args)
    environment, tab, cdp = open_selected(args)
    try:
        before = require_idle(cdp)
        result = cdp.evaluate(
            r"""
(() => {
  const direct = document.querySelector('[data-testid="create-new-chat-button"]');
  const candidates = [...document.querySelectorAll('a, button')];
  const target = direct || candidates.find(el => /^(new chat|新聊天|新对话)$/i.test((el.innerText || el.getAttribute('aria-label') || '').trim()));
  if (!target) return {ok: false, reason: 'new-chat control not found'};
  target.click();
  return {ok: true};
})()
"""
        )
        if not result or not result.get("ok"):
            raise SkillError((result or {}).get("reason", "Could not start a new ChatGPT conversation"))
        time.sleep(1.0)
        after = inspect(cdp)
    finally:
        cdp.close()
    emit(
        {
            "action": "new-chat",
            "environment": environment["environment"],
            "tab_before": tab_summary(tab),
            "before": before,
            "after": after,
        }
    )


def command_draft_or_send(args: argparse.Namespace, should_send: bool) -> None:
    require_confirm(args)
    prompt = read_prompt(args.text_file)
    environment, tab, cdp = open_selected(args)
    try:
        before = require_idle(cdp)
        fill_editor(cdp, prompt)
        if should_send:
            click_send(cdp)
            deadline = time.monotonic() + 8.0
            after = inspect(cdp)
            while after.get("user_message_count", 0) <= before.get("user_message_count", 0):
                if time.monotonic() >= deadline:
                    raise SkillError("Send was clicked, but a new user message was not observed within 8 seconds")
                time.sleep(0.4)
                after = inspect(cdp)
        else:
            after = inspect(cdp)
    finally:
        cdp.close()
    emit(
        {
            "action": "send" if should_send else "draft",
            "environment": environment["environment"],
            "tab": tab_summary(tab),
            "text_characters": len(prompt),
            "before": before,
            "after": after,
        }
    )


def command_wait(args: argparse.Namespace) -> None:
    if args.timeout <= 0:
        raise SkillError("--timeout must be positive")
    if args.interval <= 0:
        raise SkillError("--interval must be positive")
    if args.after_assistant_count is not None and args.after_assistant_count < 0:
        raise SkillError("--after-assistant-count must be non-negative")
    environment, tab, cdp = open_selected(args)
    deadline = time.monotonic() + args.timeout
    try:
        state = inspect(cdp)
        while state.get("generating") or (
            args.after_assistant_count is not None
            and state.get("assistant_message_count", 0) <= args.after_assistant_count
        ):
            if time.monotonic() >= deadline:
                if state.get("generating"):
                    reason = "ChatGPT was still generating"
                else:
                    reason = (
                        "No new assistant message appeared after count "
                        f"{args.after_assistant_count}"
                    )
                raise SkillError(f"{reason} after {args.timeout:g} seconds")
            time.sleep(args.interval)
            state = inspect(cdp)
    finally:
        cdp.close()
    emit({"environment": environment["environment"], "tab": tab_summary(tab), "state": state})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", help="Exact AdsPower environment name")
    parser.add_argument("--tab-id", help="Exact CDP target ID")
    parser.add_argument("--tab-title", help="Case-insensitive substring of the ChatGPT tab title")
    parser.add_argument(
        "--conversation-url",
        help="Exact ChatGPT /c/ conversation URL; query parameters and fragments are ignored",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover", help="List live AdsPower/SunBrowser environments")
    subparsers.add_parser("tabs", help="List ChatGPT tabs in one environment")
    subparsers.add_parser("inspect", help="Read bounded visible page state and a text excerpt")

    open_project = subparsers.add_parser(
        "open-project", help="Open an exact ChatGPT project in a new background tab"
    )
    open_project.add_argument("--project-name", required=True, help="Exact visible project name")
    open_project.add_argument(
        "--confirm", action="store_true", help="Confirm the explicitly requested background tab"
    )

    export_conversation_parser = subparsers.add_parser(
        "export-conversation",
        help="Export the complete rendered user/assistant conversation to scratch JSON",
    )
    export_conversation_parser.add_argument(
        "--output", required=True, help=f"JSON path under {DEFAULT_ROOT}"
    )

    screenshot = subparsers.add_parser("screenshot", help="Capture the visible ChatGPT viewport")
    screenshot.add_argument("--output", help=f"PNG path under {DEFAULT_ROOT}")

    new_chat = subparsers.add_parser("new-chat", help="Start a new ChatGPT conversation")
    new_chat.add_argument("--confirm", action="store_true", help="Confirm the explicitly requested mutation")

    for name in ("draft", "send"):
        mutation = subparsers.add_parser(name, help=f"{name.title()} UTF-8 text in the selected ChatGPT tab")
        mutation.add_argument("--text-file", required=True, help=f"UTF-8 file under {DEFAULT_ROOT}, or - for stdin")
        mutation.add_argument("--confirm", action="store_true", help="Confirm the explicitly requested mutation")

    select_model_parser = subparsers.add_parser(
        "select-model", help="Select an exact model label in the ChatGPT composer"
    )
    select_model_parser.add_argument("--name", required=True, help="Exact visible model label, for example Pro")
    select_model_parser.add_argument(
        "--confirm", action="store_true", help="Confirm the explicitly requested mutation"
    )

    wait = subparsers.add_parser("wait", help="Wait until ChatGPT is no longer generating")
    wait.add_argument("--timeout", type=float, default=180.0)
    wait.add_argument("--interval", type=float, default=1.0)
    wait.add_argument(
        "--after-assistant-count",
        type=int,
        help="Wait for an assistant message count greater than this value as well as idle state",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "discover":
            command_discover(args)
        elif args.command == "tabs":
            command_tabs(args)
        elif args.command == "inspect":
            command_inspect(args)
        elif args.command == "open-project":
            command_open_project(args)
        elif args.command == "export-conversation":
            command_export_conversation(args)
        elif args.command == "screenshot":
            command_screenshot(args)
        elif args.command == "new-chat":
            command_new_chat(args)
        elif args.command == "draft":
            command_draft_or_send(args, should_send=False)
        elif args.command == "send":
            command_draft_or_send(args, should_send=True)
        elif args.command == "select-model":
            command_select_model(args)
        elif args.command == "wait":
            command_wait(args)
        else:
            parser.error(f"Unknown command: {args.command}")
    except SkillError as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
