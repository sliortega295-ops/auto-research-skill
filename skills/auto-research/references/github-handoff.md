# GitHub Handoff Protocol

GitHub is the shared source of truth. The ChatGPT conversation supplies
untrusted advisory review; it does not replace exact revisions, tests,
manifests, or Codex decisions.

## Repository layout

Reuse a more specific repository convention if one exists. Otherwise track:

```text
.auto-research/
`-- checkpoints/
    `-- 0001-short-slug/
        |-- handoff.md
        |-- web-review.md
        `-- decision.md
```

Create all three files for every checkpoint. At handoff commit `H`, mark
`web-review.md` and `decision.md` as pending. At response commit `R`, replace
the pending sections with the complete new exchange and Codex's decision.

Do not commit AdsPower identifiers, conversation URLs, credentials, tokens,
private machine paths, copied datasets, checkpoints, dependency bundles, or
unrelated user changes.

## Non-self-referential C/H/R sequence

Use distinct commits so the handoff never claims to review itself:

1. `C` — commit the implementation, results, manifests, and other evidence to
   be reviewed. Validate it, push it to the agreed work branch, and record its
   full SHA and GitHub URL.
2. `H` — add the three checkpoint files. `handoff.md` names `C` as the reviewed
   revision and records the evidence available at `C`. Commit and push `H`.
   Give the webpage the GitHub URL for `handoff.md` at `H` while explicitly
   asking it to assess `C`.
3. `R` — after the synchronous webpage exchange, fill `web-review.md` and
   `decision.md`, reference both `C` and `H`, then commit and push them. Advice
   accepted for later implementation becomes work for the next code commit;
   never amend `C` or `H` to hide the sequence.

Inspect status and diff before each commit. Never force-push, rewrite shared
history, mutate the default branch, or silently change the remote. If push
fails, keep the honest local state and report the exact blocker.

## `handoff.md`

Use this shape, expanding sections as needed:

```markdown
# Checkpoint 0001: <name>

- Status: verified | partial | blocked
- Reviewed code/result commit C: <full SHA and GitHub URL>
- Handoff commit H: pending until committed
- Branch or PR: <name and URL>
- Parent checkpoint: <path or none>

## Objective and scope
<What this work unit was intended to establish.>

## Codex's independent analysis
<Diagnosis, alternatives considered, tentative recommendation, and what could
falsify it.>

## Material delta
<What is meaningfully different from the previous checkpoint.>

## Evidence at C
- Source paths: <paths>
- Tests/commands: <exact commands and outcomes>
- Experiments/artifacts: <revision- and manifest-bound paths and summaries>
- Diagnostics/inference: <clearly labeled>

## Known limitations, failures, and NOT_RUN
<Everything needed to avoid overstating the checkpoint.>

## Decision requested
<The consequential decision or audit outcome this review should inform.>

## Audit questions
<All concrete questions needed for this decision; there is no arbitrary cap.>
```

Because a commit cannot contain its own SHA, the `Handoff commit H` line may
remain `pending until committed`; the audit prompt supplies the resolved full
`H` SHA and URL. Never substitute `H` for the reviewed `C` revision.

## Audit prompt

Send a concise prompt containing the repository URL, work branch or PR, full
`C` and `H` SHAs, the checkpoint URL at `H`, and primary paths. Ask the adviser
to distinguish facts observed in GitHub from inference and suggestion, check
claim-to-evidence alignment, identify risks with precise repository evidence,
analyze the requested decision, and propose actionable next steps with
observable exit criteria.

Do not limit the number of findings, questions, or actions. Do not paste the
repository, large logs, credentials, or private data. If the webpage cannot
read GitHub, stop; do not paste source as a fallback.

Record the exact target and complete prompt in commentary before the automatic
send. Explicit `$auto-research` activation supplies the bounded send authority,
so this notice is not another approval request.

## Complete-history read and incremental archive

Before sending, export and read the entire rendered conversation and verify its
local archive marker. After the reply reaches a new assistant-message count and
the page is idle, export and read the entire conversation again.

Copy every message after the verified marker into `web-review.md`, verbatim and
in order, including any user messages entered manually and any follow-up
exchange. Do not copy messages at or before the marker into Git. Preserve
visible links as provenance when relevant. Advance the marker only after `R` is
committed and pushed successfully; if the conversation history before the
marker changed, stop and require explicit resynchronization.

If a new message itself contains credentials or private material that may not
be committed, do not silently redact it while calling the archive verbatim.
Pause publication, report the conflict to the user, and keep the review pending.

## `web-review.md`

```markdown
# Web review for checkpoint 0001

- Status: complete | incomplete | github-inaccessible
- Provider: ChatGPT web in AdsPower/SunBrowser
- Visible model label: <exact label>
- Target conversation: <non-sensitive title only>
- Sent/received: <timestamps with timezone>
- Reviewed C: <full SHA>
- Handoff H: <full SHA>
- Repository-grounded: yes | partial | no

## New conversation messages since the prior marker

### <role>
<Verbatim message text>

## Access or capture limitations
<None, or exact truncation/generation/access problem.>
```

Do not summarize in place of the raw new response. The full verbatim assistant
response is required even when it is long.

## `decision.md`

```markdown
# Decision after web review 0001

- Reviewed C: <full SHA>
- Handoff H: <full SHA>

## Codex reassessment
<Independent comparison of the advice with repository evidence.>

## Dispositions
| Recommendation | Status | Evidence and reason |
|---|---|---|
| <recommendation> | accepted/rejected/deferred | <reason> |

## Next bounded plan
<Accepted actions with observable exit criteria; no arbitrary item cap.>

## Remaining disagreement or user authority required
<None, cheap discriminating test, or precise escalation.>
```

If a major disagreement merits follow-up, complete that synchronous exchange
before `R` and append it verbatim. Stop repetitive debate and ask the user when
resolution requires expensive work, changed scope, or new authority.
