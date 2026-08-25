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
title, and expected visible model label. It does not store conversation text,
GitHub credentials, a browser tab ID, cookies, or account secrets.

Older registry entries may contain transcript archive-marker fields. They are
ignored by the GitHub-writeback workflow and need not be migrated merely to
start a consultation.

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
after verifying an intentional reassignment. A conversation cannot be bound to
multiple GitHub repositories.

The binding identifies the correct web conversation; it does not authorize
arbitrary GitHub changes. For `$auto-research`, the outgoing checkpoint prompt
must name the exact branch and the two pre-created Pro-owned files. The GitHub
commit `P`, not an exported chat transcript, is the authoritative response.

If the bound conversation is not open, ask the user to open it. Never launch,
navigate, or replace the target automatically. If the stable URL or repository
identity no longer matches, stop instead of guessing.
