# Consultation Policy

Consult the bound ChatGPT Pro conversation only when independent external
reasoning can materially improve a consequential decision or audit. This is a
judgment policy, not a numeric gate.

## Required local reasoning

Before consulting, Codex must already have:

- inspected the relevant source, repository history, tests, results, and prior
  checkpoint;
- stated the current diagnosis or milestone claim;
- identified plausible next approaches and the tentative preferred approach;
- recorded what evidence is missing and why another local check is not the
  obvious next step;
- separated measured facts from inference and adviser-facing questions.

Do not outsource first-pass understanding or ask the webpage to invent the
project plan from a repository dump.

## High-value consultation situations

Consult when there is a material delta and at least one of these situations:

- a major, validated milestone is ready for independent correctness,
  methodology, or claim audit;
- local investigation leaves a high-impact architectural, research, or
  evaluation choice genuinely ambiguous;
- new evidence contradicts the current method, evaluation plan, or paper
  claim;
- progress has plateaued after several materially different, evidence-driven
  attempts and choosing the next recovery direction is consequential;
- a PR, release, expensive experiment phase, full paper, rebuttal, or
  submission candidate is at a final-readiness boundary.

Example: a system starts at 120 seconds with an 80-second target. After several
meaningfully different, profiled approaches it remains near 95 seconds and the
remaining bottleneck admits competing strategies with substantial tradeoffs.
That is a useful recovery consultation. One slow run before profiling is not.

## Continue locally instead

Do not consult for routine syntax or build errors, ordinary debugging, one
failing test, formatting, minor refactors, locally discoverable facts, a small
completed subtask, or a question whose answer cannot change the immediate safe
next action.

Do not repeat the same question without changed evidence. Elapsed time, line
count, commit count, or the desire for reassurance is not a material delta.
When a cheap targeted check can distinguish the options, run it locally first.

## Follow-up policy

One consultation may contain a natural exchange, but follow-ups must remain
decision-focused. Continue only when:

- the response exposes a consequential misunderstanding that can be corrected
  with precise repository evidence;
- a new test or source finding changes the premise;
- the adviser proposes a new hypothesis that would alter the next high-impact
  action;
- one concise clarification would discriminate between the live options.

Stop when answers repeat, terminology is the only disagreement, or neither
side has new evidence. Prefer a cheap discriminating experiment over prolonged
argument. Escalate expensive unresolved disagreements or scope changes to the
user.

## Final-readiness rule

Use a final audit when the requested substantial deliverable is reviewable and
Codex is otherwise ready to declare completion. Ask for concrete defects,
unsupported claims, missing validation, and release/submission blockers. If
that audit cannot be performed, retain `final-audit-pending` status.
