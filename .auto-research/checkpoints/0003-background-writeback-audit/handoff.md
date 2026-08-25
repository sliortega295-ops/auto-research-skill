# Checkpoint 0003: Background GitHub writeback audit

- Status: verified
- Reviewed code/result commit C: [`068044269f345bac7b31c8db1a4d594e580b3443`](https://github.com/sliortega295-ops/auto-research-skill/commit/068044269f345bac7b31c8db1a4d594e580b3443)
- Branch: [`auto-research/initial-audit`](https://github.com/sliortega295-ops/auto-research-skill/tree/auto-research/initial-audit)
- Parent checkpoint: `.auto-research/checkpoints/0002-direct-writeback-audit` (superseded before review)
- Pro write allowlist:
  - `.auto-research/checkpoints/0003-background-writeback-audit/pro-review.md`
  - `.auto-research/checkpoints/0003-background-writeback-audit/pro-plan.md`

## Objective and scope

Audit the first usable design of two cooperating Codex skills:

- `auto-research` lets Codex execute substantial project and paper-research
  work and consult a dedicated ChatGPT Pro conversation only at consequential
  uncertainty, major milestones, stalled progress, and final readiness.
- `adspower-chatgpt` communicates with an already authenticated ChatGPT page in
  AdsPower/SunBrowser through background CDP control, without taking over the
  user's mouse, keyboard, active window, or active tab.

GitHub is the durable communication channel. Pro writes its complete audit and
proposed plan directly to the two allowlisted files. The webpage contains only
a short writeback receipt. Pro may not modify code or any other repository path.

The audit must identify comparable prior work, concrete ideas worth borrowing,
and functionality that is missing, weak, or insufficiently validated.

## Codex's independent analysis

The architecture now separates four exact states: `C` is reviewed code and
evidence, `H` is the Codex handoff, `P` is Pro's scoped GitHub writeback, and
`D` is Codex's independent adjudication. This avoids copying full conversations
and lets each participant own its durable artifacts.

The background-control requirement is essential because the user continues
working on the same desktop. The helper therefore creates a dedicated project
target with CDP `Target.createTarget(background=true)` and never calls target
activation. Ordinary send, wait, model selection, inspection, and screenshots
also operate against the selected background target.

Potential risks remain around selector drift, GitHub transaction recovery,
same-branch concurrency, post-hoc path enforcement, GitHub write provenance,
and whether the overall workflow is sufficiently distinct and useful compared
with existing planner/critic/executor and GitHub-native agent systems.

## Material delta

Since the last reviewed implementation candidate:

- changed AdsPower control from GUI-first to background-CDP-first;
- explicitly prohibits X11 activation, mouse movement, clicking, and keyboard
  input whenever the user may be working;
- added an exact-name `open-project` command that discovers an authenticated
  ChatGPT project link and opens it as a separate background target;
- requires the new target to remain hidden and treats unexpected visibility as
  failure;
- added tests that verify project URL validation, exact/deduplicated project
  discovery, and the absence of any target-activation call;
- retained direct Pro GitHub writeback to two exact checkpoint files and no
  complete-conversation export in `$auto-research`.

## Evidence at C

- AdsPower helper unit tests: 12 passed.
- Auto-research registry unit tests: 4 passed.
- Repository and installed copies of both skills passed `quick_validate.py`.
- Installed and repository skill copies matched byte-for-byte, excluding
  generated `__pycache__` directories.
- `git diff --check` passed before C.

## Known limitations, failures, and NOT_RUN

- A live background `open-project` operation has not yet been performed; the
  command is unit-tested but still needs an end-to-end check in this exact
  AdsPower session.
- A live Pro-authored GitHub writeback has not yet been completed.
- The file allowlist is verified after the remote commit rather than enforced
  as a per-path GitHub permission.
- Recovery from multiple Pro commits, branch divergence, partial writeback, or
  a false success receipt is specified but not live-tested.
- Project-link and composer DOM selectors can drift with ChatGPT UI changes.
- No outcome data yet establishes that sparse Pro consultations improve quality
  enough to justify latency.

## Decision requested

Determine whether this background, direct-GitHub-writeback design is sound
enough for an initial release and prioritize the improvements required before
using it for substantial software and paper research.

## Audit questions

1. What papers, open-source projects, agent frameworks, or GitHub-native
   workflows are genuinely comparable? Provide direct links and architectural
   comparisons rather than a generic product list.
2. Which concrete mechanisms from those systems should this project borrow,
   where would each fit, and what complexity would it add?
3. Which safety, recovery, integrity, provenance, concurrency, usability, or
   validation properties remain missing or weak?
4. Are `C/H/P/D`, the two-file Pro write allowlist, and short webpage receipt a
   clear enough authority boundary?
5. Is direct same-branch writeback appropriate, or would a response branch, PR,
   issue, or signed artifact materially improve safety without making the
   workflow cumbersome?
6. Prioritize recommendations with observable exit criteria. Clearly separate
   repository-verified findings from inference and proposals.

## Write instructions for ChatGPT Pro

Write the complete audit only to `pro-review.md` and the complete proposed plan
only to `pro-plan.md`, then commit only those two files to branch
`auto-research/initial-audit`. Do not modify code, tests, configurations,
documentation, scripts, existing checkpoints, or `decision.md`.
