# Checkpoint 0002: Direct GitHub writeback audit

- Status: verified
- Reviewed code/result commit C: [`80c5361e049fe9af2268857a173b5c0efe352f6c`](https://github.com/sliortega295-ops/auto-research-skill/commit/80c5361e049fe9af2268857a173b5c0efe352f6c)
- Branch: [`auto-research/initial-audit`](https://github.com/sliortega295-ops/auto-research-skill/tree/auto-research/initial-audit)
- Parent checkpoint: `.auto-research/checkpoints/0001-initial-skill-audit`
- Pro write allowlist:
  - `.auto-research/checkpoints/0002-direct-writeback-audit/pro-review.md`
  - `.auto-research/checkpoints/0002-direct-writeback-audit/pro-plan.md`

## Objective and scope

Audit the revised `auto-research` and `adspower-chatgpt` skills. The intended
workflow combines ChatGPT Pro's planning and audit strengths with Codex's local
execution and validation. GitHub carries the durable handoff:

- Codex pushes exact code, evidence, and a checkpoint.
- ChatGPT Pro reads that revision and writes its complete audit and proposed
  next plan directly to the two allowlisted checkpoint files.
- The webpage reply is only a short commit receipt and summary.
- Codex verifies the Pro commit changed no code or other path, independently
  adjudicates every recommendation, and then continues execution.

The review should also identify genuinely comparable prior work, ideas worth
borrowing, and missing or weak functionality in this implementation.

## Codex's independent analysis

The revised protocol is materially simpler than transcript mirroring. It uses
GitHub as the only durable shared state and separates authorship through a
`C/H/P/D` sequence: code, handoff, Pro response, and Codex decision. Pre-created
file ownership and post-commit path verification limit Pro to advisory content
without treating its GitHub access as read-only.

The main unresolved risks are transaction recovery, concurrent branch changes,
the reliability of Pro's GitHub write action, provenance quality inside its
review, and whether a direct same-branch write is preferable to a PR or
dedicated response branch. These are hypotheses for audit, not established
defects.

## Material delta

Compared with checkpoint 0001 and commit `7138cae`:

- removed complete ChatGPT transcript export and incremental archive markers
  from the `auto-research` protocol;
- replaced `C/H/R` with `C/H/P/D`, where Pro authors and commits its own review
  and proposed-plan files;
- restricted Pro writes to two exact pre-created checkpoint paths while
  explicitly prohibiting source, test, config, evidence, and Codex-owned file
  changes;
- made the webpage response a compact `WRITEBACK/COMMIT/FILES/SUMMARY` receipt;
- changed AdsPower guidance to prefer visible GUI interaction for ordinary
  send/wait actions and reserve the helper for cases needing exact targeting or
  structured extraction;
- removed transcript marker commands and tests from the project registry.

## Evidence at C

- `python3 -m unittest discover -s skills/auto-research/tests -p 'test_*.py' -v`
  — 4 tests passed.
- `python3 -m unittest discover -s skills/adspower-chatgpt/tests -p 'test_*.py' -v`
  — 9 tests passed.
- Both repository skills and both installed copies passed the Codex
  `quick_validate.py` validator.
- Installed and repository copies were byte-for-byte identical after the
  change, excluding `__pycache__`.
- `git diff --check` passed before commit C.

## Known limitations, failures, and NOT_RUN

- A live Pro-authored GitHub writeback has not yet been completed.
- The path allowlist is enforced by Codex after the remote commit, not by a
  GitHub App permission that can express per-file restrictions.
- Recovery after a Pro partial write, multiple commits, remote divergence, or
  an incorrect success receipt is specified but not end-to-end tested.
- The current protocol pauses local writes during Pro review; concurrent Codex
  execution is intentionally not supported.
- No quantitative evidence yet shows that sparse consultations improve project
  outcomes enough to justify their latency.
- Comparable academic and open-source systems have not yet been systematically
  mapped.

## Decision requested

Determine whether the direct GitHub writeback architecture is sound enough for
an initial working release and which improvements should be prioritized before
using it for substantial project and paper research.

## Audit questions

1. What papers, open-source projects, agent frameworks, or GitHub-native
   workflows are genuinely comparable? Provide direct links and architectural
   comparisons, not a generic product list.
2. Which concrete mechanisms from those systems should this project borrow,
   and where would each fit?
3. Are the `C/H/P/D` stages and two-file Pro write allowlist sufficient to keep
   authorship, evidence, and execution authority clear?
4. Which recovery, concurrency, integrity, provenance, security, or UX cases
   remain missing or weak?
5. Is direct same-branch writeback appropriate, or would a dedicated response
   branch, PR, issue, or signed artifact be materially safer without making the
   workflow cumbersome?
6. Prioritize the recommended changes with observable exit criteria. Separate
   repository-verified findings from inference and proposals.

## Write instructions for ChatGPT Pro

Write the complete audit only to `pro-review.md` and the complete proposed plan
only to `pro-plan.md`, then commit only those two files to branch
`auto-research/initial-audit`. Do not modify code, tests, configurations,
documentation, scripts, existing checkpoint files, or `decision.md`.
