# GitHub Handoff Protocol

GitHub is the shared source of truth. ChatGPT Pro writes its complete review
and proposed plan into narrowly scoped checkpoint files; its webpage reply is
only a short completion receipt. Codex independently verifies the commit and
decides what to accept.

## Repository layout and ownership

Reuse a more specific repository convention if one exists. Otherwise track:

```text
.auto-research/
`-- checkpoints/
    `-- 0001-short-slug/
        |-- handoff.md       # Codex-owned request and evidence
        |-- pro-review.md    # Pro-owned audit
        |-- pro-plan.md      # Pro-owned proposed next plan
        `-- decision.md      # Codex-owned adjudication
```

Codex creates all four files before consultation. Pro may update only the two
pre-created Pro-owned files for the active checkpoint. It must not change
source code, tests, configurations, manifests, papers, experiment artifacts,
other checkpoints, `handoff.md`, or `decision.md`.

Do not commit AdsPower identifiers, conversation URLs, credentials, tokens,
private machine paths, copied datasets, checkpoints, dependency bundles, or
unrelated user changes.

## C/H/P/D sequence

Keep the stages distinct so every claim names an exact reviewed revision:

1. `C` — Codex commits the implementation, results, manifests, and evidence to
   be reviewed. Validate and push it to the agreed work branch.
2. `H` — Codex adds the four checkpoint files. `handoff.md` names `C`, while
   `pro-review.md`, `pro-plan.md`, and `decision.md` are pending. Commit and
   push `H`, then stop local repository writes for the duration of the review.
3. `P` — Pro reads `C` and `H`, replaces only the two Pro-owned pending files,
   and commits them directly to the same work branch. The webpage reply reports
   the write status, `P` SHA, changed paths, and a brief summary.
4. `D` — Codex fetches and verifies `P`, fast-forwards only after the scope
   check passes, independently adjudicates the advice in `decision.md`, and
   commits and pushes `D`. Accepted work begins in a later code commit; do not
   rewrite `C`, `H`, or `P`.

Before each Codex commit, inspect status and diff. Never force-push, rewrite
shared history, change repository visibility, or silently change the remote.
If a push or fast-forward fails, keep the honest state and report the blocker.

## Handoff content

Use this shape, expanding sections as needed:

```markdown
# Checkpoint 0001: <name>

- Status: verified | partial | blocked
- Reviewed code/result commit C: <full SHA and GitHub URL>
- Branch or PR: <name and URL>
- Parent checkpoint: <path or none>
- Pro write allowlist:
  - `.auto-research/checkpoints/0001-<slug>/pro-review.md`
  - `.auto-research/checkpoints/0001-<slug>/pro-plan.md`

## Objective and scope
<What this work unit was intended to establish.>

## Codex's independent analysis
<Diagnosis, alternatives, tentative recommendation, and falsifiers.>

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
<Concrete questions needed for this decision; there is no arbitrary cap.>
```

## Audit prompt and webpage receipt

Send a concise prompt containing the repository URL, work branch, full `C` and
`H` SHAs, checkpoint URL at `H`, and the two exact writable paths. Ask Pro to:

- distinguish repository observations from inference and proposals;
- check claim-to-evidence alignment and identify precise risks;
- write the complete audit to `pro-review.md`;
- write the proposed next steps and observable exit criteria to `pro-plan.md`;
- commit only those two files to the named branch;
- leave a short webpage receipt rather than repeating the full review.

The receipt should be easy to verify visually:

```text
WRITEBACK: complete | blocked
COMMIT: <full SHA or none>
FILES: <the two allowed paths actually changed>
SUMMARY: <one short paragraph or exact blocker>
```

Do not ask Pro to modify code or implement its own plan. Do not paste the
repository, large logs, credentials, or private data into the conversation.
Record the exact target and complete outgoing prompt in commentary before the
automatic send.

## Verify P before using it

After the webpage reports completion:

1. Fetch the named remote branch without merging.
2. Resolve `P` from the receipt and remote history; require it to descend from
   `H` without an unrelated branch rewrite.
3. Inspect `P`'s changed paths and content. Require the changed-path set to be a
   non-empty subset of the two allowlisted files. Treat any source, config,
   test, evidence, or other checkpoint change as out of scope.
4. Verify the review names `C`, is repository-grounded, and preserves honest
   unknown, partial, failed, and `NOT_RUN` states.
5. Fast-forward the clean local work branch only after all checks pass.

If Pro reports success but no matching commit exists, the branch diverges, or
an out-of-scope path changed, stop. Do not execute the proposed plan, rewrite
the remote commit, or infer the missing review from the chat receipt.

## `pro-review.md`

```markdown
# Pro review for checkpoint 0001

- Status: complete | partial | github-inaccessible | github-write-failed
- Reviewed C: <full SHA>
- Handoff H: <full SHA>
- Repository-grounded: yes | partial | no

## Executive assessment
<Concise overall judgment.>

## Verified findings
<Findings with repository paths, commits, tests, or artifacts.>

## Risks, gaps, and unsupported claims
<Prioritized issues and why they matter.>

## Open questions and uncertainty
<Facts not established from the repository.>
```

## `pro-plan.md`

```markdown
# Pro proposed plan for checkpoint 0001

- Based on C: <full SHA>
- Based on H: <full SHA>

## Recommended next actions
<Ordered actions with rationale and observable exit criteria.>

## Alternatives and trade-offs
<Consequential choices that Codex should adjudicate.>

## Suggested validation
<Tests, experiments, or audits; do not claim they were run.>
```

## `decision.md`

```markdown
# Codex decision after Pro review 0001

- Reviewed C: <full SHA>
- Handoff H: <full SHA>
- Pro commit P: <full SHA>

## Codex reassessment
<Independent comparison of the advice with repository evidence.>

## Dispositions
| Recommendation | Status | Evidence and reason |
|---|---|---|
| <recommendation> | accepted/rejected/deferred | <reason> |

## Next bounded plan
<Accepted actions with observable exit criteria.>

## Remaining disagreement or user authority required
<None, a cheap discriminating test, or a precise escalation.>
```

If a major disagreement merits follow-up, ask Pro to update the same two files
in a new scoped commit after receiving new evidence. Stop repetitive debate and
ask the user when resolution requires expensive work, changed scope, or new
authority.
