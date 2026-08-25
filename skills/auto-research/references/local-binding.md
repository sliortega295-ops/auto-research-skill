# Local Project Binding

Each GitHub repository maps to exactly one manually created, already-open
ChatGPT conversation. The mapping is local and must never be committed.

## Registry

The helper stores private data at:

```text
~/.codex/auto-research/targets.json
```

When `CODEX_HOME` is set, use `$CODEX_HOME/auto-research/targets.json` instead.

The registry key is the canonical `github.com/owner/repository` origin, so
another clone of the same origin resolves the same binding. Each entry stores
the AdsPower environment, canonical `/c/` conversation URL, human-readable
title, expected visible model label, and last archived message marker. It does
not store a tab ID, cookies, credentials, or conversation text.

## Bind or inspect

The user must first create and open the dedicated conversation in AdsPower.
Resolve its stable URL read-only, then run:

```bash
registry_helper="${CODEX_HOME:-$HOME/.codex}/skills/auto-research/scripts/project_registry.py"

python3 "$registry_helper" bind \
  --repo /absolute/project/path \
  --environment YOUR_ADSPOWER_ENV \
  --conversation-url 'https://chatgpt.com/.../c/<conversation-id>' \
  --conversation-title 'Project review' \
  --model-label Pro

python3 "$registry_helper" get --repo /absolute/project/path
python3 "$registry_helper" list
```

Binding is idempotent when the identity is unchanged. Use `--replace` only
after verifying an intentional reassignment. Replacing the conversation URL
resets its archive marker. A conversation cannot be bound to multiple GitHub
repositories.

## Export, compare, and archive

Use `$adspower-chatgpt` with the binding's exact environment and conversation
URL. Store exports under disposable scratch:

```bash
browser_helper="${CODEX_HOME:-$HOME/.codex}/skills/adspower-chatgpt/scripts/adspower_chatgpt.py"
transcript='/tmp/lyy-experiments/adspower-chatgpt/<run-id>/conversation.json'

python3 "$browser_helper" \
  --environment YOUR_ADSPOWER_ENV \
  --conversation-url 'https://chatgpt.com/.../c/<conversation-id>' \
  export-conversation --output "$transcript"

python3 "$registry_helper" pending \
  --repo /absolute/project/path \
  --transcript "$transcript"
```

`pending` verifies the export's environment, canonical URL, message indexes,
message hashes, and previous archive marker. Codex still reads the complete
JSON; the command only identifies which suffix is new.

On first binding, read the complete existing history and deliberately set it as
the baseline before sending the first checkpoint. After a review, advance the
marker only after response commit `R` is committed and pushed successfully:

```bash
python3 "$registry_helper" mark-archived \
  --repo /absolute/project/path \
  --transcript "$transcript"
```

If the bound conversation is not open, ask the user to open it. Never launch,
navigate, or replace the target automatically. If marker validation fails,
stop rather than guessing where the incremental history begins.
