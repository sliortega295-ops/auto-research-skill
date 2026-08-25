---
name: auto-research
description: Run an explicitly invoked, durable research and development loop in which Codex executes and a dedicated ChatGPT Pro webpage occasionally audits the work and writes review and proposed-plan artifacts directly to GitHub checkpoints. Use only when the user explicitly names $auto-research; never activate it implicitly for ordinary coding, browsing, or research tasks.
---

# Auto Research

Coordinate substantial project work between Codex and one dedicated ChatGPT
web conversation. Codex owns source inspection, implementation, experiments,
validation, independent reasoning, and every final decision. The webpage is an
advisory planner and auditor that may write only its assigned checkpoint
artifacts. GitHub is the shared, versioned source of truth; the chat transcript
is not a second archive.

This is a controller skill. Invoke relevant domain skills for coding,
profiling, literature, experiment design, paper writing, or submission checks
when their own triggers apply.

## Activation boundary

Run only after the user explicitly invokes `$auto-research`. Use the user's
plan as the initial plan and begin local execution; do not request a kickoff
review from the webpage.

For the active invocation, the user grants these bounded standing permissions:

- commit and push task-scoped changes to the already agreed GitHub work branch;
- select the binding's exact visible model label and send qualifying review
  packets to the bound ChatGPT conversation without seeking approval again;
- ask that bound adviser to update and commit only the pre-created
  `pro-review.md` and `pro-plan.md` files for the active checkpoint.

This does not authorize committing unrelated user changes, modifying or
force-pushing the default branch, rewriting history, changing remotes or
repository visibility, merging a PR, publishing a release, spending
substantial resources, or contacting any other conversation or person. If the
checked-out branch is the default branch or the work branch is ambiguous, ask
the user to identify the work branch before publishing.

The webpage must not modify source code, tests, configurations, manifests,
experiment outputs, papers, existing evidence, `handoff.md`, or `decision.md`.
Giving it GitHub write access does not expand the project's scope or make its
recommendations authoritative.

## Establish or recover the project contract

Before changing the repository:

1. Read the applicable `AGENTS.md` files and inspect the live repository,
   working tree, branch, upstream, remote, and existing project conventions.
2. Recover the user's objective, supplied plan, deliverables, success criteria,
   correctness/evaluation contract, exclusions, and resource limits. Preserve
   honest `NOT_RUN`, partial, and failed outcomes.
3. Resolve the local repository-to-conversation binding. Read
   [local-binding.md](references/local-binding.md) for the registry workflow.
4. Confirm that the origin is `github.com`, the work branch is agreed and
   publishable, and the dedicated conversation is already open in its stored
   AdsPower environment.

Use one dedicated ChatGPT conversation per project. Prefer an existing bound
conversation. When the user explicitly requests a fresh conversation in a
named ChatGPT project, create it as a new background CDP target without
activating the browser window or tab; never reuse or navigate one of the user's
other conversations. Bind the resulting stable conversation URL, not its
temporary target ID or tab order. Keep the AdsPower environment, conversation
URL/title, and model label only in the local registry; never commit them.

The expected visible model label is `Pro` unless the binding says otherwise.
For this workflow, record that as the currently visible ChatGPT 5.6 Pro choice;
do not claim access to an internal model identifier that the page does not
expose.

## Execute coherent work units

Work autonomously in substantial, reviewable units:

1. Recover the latest verified state, unresolved decisions, prior checkpoint,
   and uncommitted user work.
2. Analyze the problem independently. Inspect source and evidence, form a
   diagnosis, compare plausible approaches, and state a tentative choice before
   asking the webpage anything.
3. Implement the coherent unit while preserving unrelated changes.
4. Validate in proportion to risk. Bind measurements to the exact revision,
   configuration, data, hardware, seeds, and procedure needed to interpret
   them.
5. Decide whether web advice now has real decision value. Read
   [consultation-policy.md](references/consultation-policy.md).

Do not consult after every edit, test, or small success. Continue locally while
the next step is clear and inexpensive to distinguish with repository evidence.
There is no consultation counter, score, or fixed message allowance.

## Consult through a GitHub checkpoint

When consultation is justified, follow
[github-handoff.md](references/github-handoff.md) exactly. Its core sequence is:

1. `C`: commit and push the code, results, and evidence to review.
2. `H`: create a checkpoint containing `handoff.md`, pending `pro-review.md`
   and `pro-plan.md` files, and a pending `decision.md`; make the handoff
   reference the full `C` SHA, then commit and push it.
3. Inspect the exact bound background conversation by stable URL without
   activating its window or tab. If an existing bound conversation is not
   open, ask the user to open it; do not repurpose another tab.
4. Verify the page is idle. Select the stored visible model label if needed,
   record the exact target and prompt in commentary, and send a concise review
   request containing the exact GitHub revision, branch, checkpoint URL, and
   the two paths the adviser may write.
5. Ask the adviser to write its complete audit to `pro-review.md`, its proposed
   next plan to `pro-plan.md`, and commit those two files as `P`. Its webpage
   reply should be only a short receipt: write status, commit SHA, paths, and a
   brief summary or blocker.
6. Wait synchronously in the background, without a preset timeout, for that
   receipt and for the page to become idle. Pro reasoning can routinely exceed
   ten minutes. Do not export the conversation, take foreground control, or
   work on other project tasks while waiting.
7. Fetch GitHub and verify that `P` descends from `H` and changes only the two
   allowed files in the active checkpoint. Stop on any source-code or
   out-of-scope change; do not execute or silently repair it.
8. Read the committed review and plan, independently adjudicate them in
   `decision.md`, then commit and push Codex decision commit `D`.

If ChatGPT cannot read the referenced GitHub revision, stop that consultation,
record it as not repository-grounded, and report the access problem. Do not
paste source code or large logs into the conversation as a fallback.

If it can read but cannot write the two assigned files, keep the checkpoint as
`github-write-pending`. Do not silently fall back to exporting or committing a
long chat transcript; ask the user before changing the handoff mechanism.

## Adjudicate; do not obey

Classify each substantive recommendation as `accepted`, `rejected`, or
`deferred`, with repository evidence and reasoning. Advice never grants scope,
permissions, factual truth, or experimental validity.

A disagreement is major only when accepting the advice would change the next
high-impact action, core method, evaluation contract, central claim, or
substantial resource use. For a major disagreement:

- prefer a cheap experiment or source check that discriminates between the
  competing hypotheses;
- send a follow-up only when new evidence or a genuinely new hypothesis makes
  the answer decision-relevant;
- stop when the exchange becomes repetitive or semantic rather than
  evidence-bearing;
- ask the user when resolving it would require expensive work, a scope change,
  or new authority.

The adviser may return as many findings, questions, or next actions as the
problem requires. Do not impose an arbitrary output-length or item-count cap.

## Completion rule

A substantial final delivery must receive a final web audit of the reviewable
candidate. If the bound conversation, expected model, GitHub access, or reply
is unavailable, report the implementation and validation state but keep the
overall result explicitly `final-audit-pending`; do not claim the delegated
auto-research project is complete.

Finish with the exact branch and `C`, `H`, `P`, and `D` SHAs, checkpoint URL,
validation status, advice dispositions, remaining uncertainty, and next bounded
action. Keep measurements, diagnostics, theory, adviser suggestions, and
planned experiments distinct.
