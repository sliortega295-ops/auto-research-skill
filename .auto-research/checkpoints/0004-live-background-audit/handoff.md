# Checkpoint 0004: Live-validated background writeback audit

- Status: verified
- Reviewed code/result commit C: [`763b456f2cc47cb8f088bcf0ca77c9c6318f631c`](https://github.com/sliortega295-ops/auto-research-skill/commit/763b456f2cc47cb8f088bcf0ca77c9c6318f631c)
- Branch: [`auto-research/initial-audit`](https://github.com/sliortega295-ops/auto-research-skill/tree/auto-research/initial-audit)
- Parent checkpoint: `.auto-research/checkpoints/0003-background-writeback-audit` (superseded before review)
- Pro write allowlist:
  - `.auto-research/checkpoints/0004-live-background-audit/pro-review.md`
  - `.auto-research/checkpoints/0004-live-background-audit/pro-plan.md`

## Objective and scope

Audit two cooperating Codex skills intended for long-running software and paper
research:

- `auto-research`: Codex executes and validates independently, consulting a
  dedicated ChatGPT Pro conversation only for consequential uncertainty,
  substantial milestones, stalled progress, and final readiness.
- `adspower-chatgpt`: a background-CDP bridge to the user's existing
  authenticated AdsPower/SunBrowser session that does not take over the mouse,
  keyboard, active window, or foreground tab.

GitHub is the durable communication channel. Pro writes its complete audit and
proposed plan directly to the two allowlisted files. Its webpage response is
only a short receipt. Pro must not modify code or any other repository path.

The review must identify genuinely comparable work, mechanisms worth borrowing,
and important functionality that remains absent or weak.

## Codex's independent analysis

The design separates exact authorship and revision state through `C/H/P/D`:
reviewed code/evidence, Codex handoff, Pro writeback, and Codex adjudication.
This removes transcript mirroring while keeping Pro advisory rather than
executable authority.

Background isolation is a hard usability requirement because the user works on
the same desktop. The live path now opens a fresh hidden ChatGPT target, expands
an exact named project if necessary, invokes its explicit `Open project home`
control, and verifies that the resulting project editor remains hidden. Send,
wait, model selection, inspection, and screenshot operations use that target's
CDP channel and never activate it.

Remaining risks likely include DOM drift, same-branch concurrency, partial or
multiple Pro commits, post-hoc rather than pre-write path enforcement, review
provenance, and whether the workflow's added ceremony produces measurable
quality improvements.

## Material delta

The candidate now includes:

- direct Pro GitHub writeback to `pro-review.md` and `pro-plan.md` only;
- a short `WRITEBACK/COMMIT/FILES/SUMMARY` webpage receipt instead of full
  conversation export;
- background-CDP-first operation and an explicit ban on foreground X11 input
  while the user may be working;
- exact project-name discovery plus a safe fallback for ChatGPT projects that
  are represented by expandable controls rather than links;
- creation of a separate hidden project target with no target-activation call;
- cleanup of task-created background targets after failed attempts;
- simplified local binding with no transcript archive-marker workflow.

## Evidence at C

- AdsPower helper unit tests: 12 passed.
- Auto-research registry unit tests: 4 passed.
- Both repository skills and installed copies passed `quick_validate.py`.
- Installed and repository copies matched byte-for-byte after validation,
  excluding generated `__pycache__` directories.
- Live background project opening succeeded in the existing authenticated
  AdsPower session: the intended project editor was present, the new target
  reported `visibility=hidden`, and the active X11 window ID was unchanged.
- Three prior failed live attempts also left the active window unchanged and
  automatically closed their task-created background targets.
- No mouse movement, keyboard injection, window activation, or foreground tab
  switch was used during the successful path.

## Known limitations, failures, and NOT_RUN

- The first live Pro prompt, reply, and GitHub writeback have not yet completed.
- File scope is verified after P reaches GitHub; GitHub permissions do not
  enforce a two-path allowlist before the write.
- Recovery after multiple commits, branch divergence, a partial write, or a
  false success receipt is specified but not end-to-end tested.
- Exact UI labels and DOM structure may change with ChatGPT releases.
- No outcome data yet establishes the quality/latency benefit of sparse Pro
  consultation.
- Comparable academic and open-source systems have not yet been systematically
  mapped.

## Decision requested

Determine whether this live-validated background and direct-writeback design is
sound enough for an initial release, and prioritize what should be improved
before it coordinates substantial project and paper research.

## Audit questions

1. What papers, open-source projects, agent frameworks, or GitHub-native
   workflows are genuinely comparable? Provide direct links and architectural
   comparisons rather than a generic product list.
2. Which concrete mechanisms from those systems should this project borrow,
   where would each fit, and what trade-off would it add?
3. Which recovery, concurrency, integrity, provenance, safety, usability, or
   validation cases remain missing or weak?
4. Are `C/H/P/D`, the two-file Pro write allowlist, and short webpage receipt a
   sufficiently clear authority boundary?
5. Is direct same-branch writeback appropriate, or would a response branch, PR,
   issue, or signed artifact materially improve safety without excessive
   ceremony?
6. Prioritize recommendations with observable exit criteria. Separate facts
   verified from this repository from inference and proposals.
7. Audit the repository for removable redundancy: duplicated code or control
   paths, overlapping skill responsibilities, dead compatibility layers,
   repeated documentation, unnecessary abstractions, and ceremony that does
   not materially improve safety or research quality. For every deletion or
   consolidation candidate, cite the exact paths or mechanisms, explain why it
   is redundant, state the regression risk, and give a post-change validation
   check. Do not recommend deletion merely to reduce line count.
8. Identify design choices that are brittle, over-coupled, hard to recover,
   difficult to test, or needlessly complex. Distinguish defects that should be
   fixed before initial use from deliberate trade-offs and optional cleanup,
   then include a safely ordered simplification plan with observable exit
   criteria.

## Write instructions for ChatGPT Pro

Write the complete audit only to `pro-review.md` and the complete proposed plan
only to `pro-plan.md`, then commit only those two files to branch
`auto-research/initial-audit`. Do not modify code, tests, configurations,
documentation, scripts, existing checkpoints, or `decision.md`.
