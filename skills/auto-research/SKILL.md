---
name: auto-research
description: Run an explicitly invoked, durable research and development loop in which Codex executes and a dedicated ChatGPT Pro webpage provides occasional planning and audit advice through GitHub checkpoints. Use only when the user explicitly names $auto-research; never activate it implicitly for ordinary coding, browsing, or research tasks.
---

# Auto Research

Coordinate substantial project work between Codex and one dedicated ChatGPT
web conversation. Codex owns source inspection, implementation, experiments,
validation, independent reasoning, and every final decision. The webpage is an
advisory planner and auditor. GitHub is the shared, versioned source of truth.

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
  packets to the bound ChatGPT conversation without seeking approval again.

This does not authorize committing unrelated user changes, modifying or
force-pushing the default branch, rewriting history, changing remotes or
repository visibility, merging a PR, publishing a release, spending
substantial resources, or contacting any other conversation or person. If the
checked-out branch is the default branch or the work branch is ambiguous, ask
the user to identify the work branch before publishing.

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

The user manually creates and opens one dedicated ChatGPT conversation per
project. Never create, open, or navigate to that conversation automatically.
Bind by stable conversation URL, not tab ID or tab order. Keep the AdsPower
environment, conversation URL/title, model label, and archive marker only in
the local registry; never commit them.

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
2. `H`: create a checkpoint containing `handoff.md`, a pending
   `web-review.md`, and a pending `decision.md`; make the handoff reference the
   full `C` SHA, then commit and push it.
3. Inspect the exact bound conversation by stable URL. If it is not already
   open, ask the user to open it; do not navigate there.
4. Export and read the complete rendered conversation. Verify the stored
   archive marker and use only the newly unarchived messages in the checkpoint.
5. Verify the page is idle. Select the stored visible model label if needed,
   record the exact target and prompt in commentary, and send the review packet.
6. Wait synchronously for a new assistant message and idle state. Do not work
   on other project tasks while waiting.
7. Export and read the complete conversation again. Preserve every new message
   verbatim in `web-review.md`; do not commit the older conversation history.
8. Independently adjudicate the advice in `decision.md`, then create and push
   response/decision commit `R`. Advance the local archive marker only after
   the review record is committed and pushed successfully.

If ChatGPT cannot read the referenced GitHub revision, stop that consultation,
record it as not repository-grounded, and report the access problem. Do not
paste source code or large logs into the conversation as a fallback.

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

Finish with the exact branch and SHAs, checkpoint URL, validation status,
advice dispositions, remaining uncertainty, and next bounded action. Keep
measurements, diagnostics, theory, adviser suggestions, and planned experiments
distinct.
