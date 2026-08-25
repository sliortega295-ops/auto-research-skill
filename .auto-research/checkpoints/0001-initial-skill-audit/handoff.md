# Checkpoint 0001: Initial skill audit

## Status

- Workflow stage: awaiting web review
- Repository: https://github.com/sliortega295-ops/auto-research-skill
- Visibility: private
- Branch: `auto-research/initial-audit`
- Code commit C: `7138caecc9041e3c2f724cfecbc212bac6661944`
- Code commit URL: https://github.com/sliortega295-ops/auto-research-skill/commit/7138caecc9041e3c2f724cfecbc212bac6661944

## Audit objective

Audit the first working version of two cooperating Codex skills:

- `skills/auto-research`: a GitHub-mediated protocol in which Codex performs
  project execution and validation, while a ChatGPT web conversation is used
  selectively for high-value planning and audit advice.
- `skills/adspower-chatgpt`: a local, fail-closed bridge for inspecting and
  interacting with an already-running ChatGPT conversation in
  AdsPower/SunBrowser.

The audit should determine whether comparable work already exists, what ideas
from it are worth borrowing, and which parts of this implementation are absent,
weak, or insufficiently validated.

## Intended operating contract

1. Codex remains the executor and final decision-maker.
2. Web consultation is advisory and deliberately infrequent: use it at a major
   milestone, before a consequential branch when the next plan is genuinely
   unclear, after repeated failure, or for a final audit.
3. Source, results, and handoff artifacts travel through exact Git commits and
   GitHub links rather than pasted code.
4. Each consultation uses three durable checkpoints:
   - C: pushed code/results commit;
   - H: pushed handoff with pending review and decision files;
   - R: pushed raw new web messages plus Codex's accepted/rejected/deferred
     decision record.
5. The bound web conversation is read in full for context, but only the new
   suffix since the archive marker is committed.
6. Browser mutation is explicit, scoped to one exact conversation, and guarded
   by confirmation flags and post-action verification.
7. If the web model cannot access the referenced GitHub material, the workflow
   stops with `github-inaccessible`; it does not silently paste code or make a
   private repository public.

## Codex preliminary assessment

### Observed strengths

- The consultation trigger is milestone/risk based rather than per-step.
- Authority boundaries are explicit: the web model advises; Codex independently
  checks evidence and decides.
- Exact commit references and C/H/R checkpoints make consultation state
  reviewable and resumable by a human.
- The local registry binds one canonical GitHub repository to one exact browser
  environment and canonical conversation URL, and fails closed on mismatches.
- Transcript handling verifies incremental history and records hashes before an
  archive marker can advance.
- Browser automation distinguishes read-only inspection from confirmed
  mutation, verifies the selected model, requires a new assistant message plus
  idle state, writes private exports with mode `0600`, and restores the scroll
  position after full-history export.

### Suspected gaps and risks to investigate

- Comparable planner/critic/executor, autonomous-research, software-agent, and
  GitHub-native agent systems likely exist; this implementation's novelty and
  best scope are not yet established against them.
- The workflow is a protocol plus local scripts, not yet a durable state machine
  with transaction recovery, locking, retries, or concurrent-project handling.
- GitHub accessibility is assumed until the web model proves it can read the
  exact private commit; there is no preflight for the web session's GitHub auth.
- ChatGPT project navigation and new-conversation creation still rely on live UI
  inspection outside the main helper; selectors may drift.
- There is no single command that scaffolds a checkpoint, creates C/H/R commits,
  generates the audit prompt, waits, archives, and resumes safely.
- There is no end-to-end mutation test against a disposable web conversation;
  the live validation so far was read-only.
- The registry currently targets GitHub repository identities and does not
  describe forks, repository transfers, non-GitHub remotes, or multiple audit
  conversations per project.
- Committing verbatim web output can conflict with secret/privacy policy; the
  exact redaction-versus-verbatim rule needs a more operational design.
- Failure recovery is described but not exhaustively modeled for partial pushes,
  a reply arriving after timeout, web edits/regeneration, or history truncation.
- There is no quantitative policy or telemetry showing that consultation is
  infrequent enough and improves outcomes enough to justify latency and cost.

These are preliminary hypotheses, not accepted audit conclusions.

## Evidence available at C

- `skills/auto-research/tests`: 7 unit tests passed.
- `skills/adspower-chatgpt/tests`: 9 unit tests passed.
- Both copied skills passed the Codex skill `quick_validate.py` validator.
- A prior read-only live check exported all 10 rendered messages (24,797
  characters) from an existing Pro conversation, verified full-history
  traversal, and restored the prior scroll position.
- The copied tree was scanned for known access tokens, browser environment IDs,
  tab IDs, and conversation IDs; no known sensitive/session values were found.

## Not run or not yet proven

- Creating a fresh conversation inside the `auto research` ChatGPT project.
- Sending an audit prompt and waiting for a new Pro response.
- The Pro web session's ability to access this private GitHub repository.
- A complete C/H/R cycle using a live mutable conversation.
- Recovery after interruption at each intermediate state.
- Concurrent repository or conversation operation.

## Questions for the web auditor

Please inspect the repository at the exact branch and commits above, especially
the two `SKILL.md` files, their references, scripts, and tests. Then answer:

1. What existing papers, open-source projects, agent frameworks, or workflow
   patterns are genuinely similar? Provide names and direct links, and compare
   their architecture and scope with this implementation rather than merely
   listing generic agent products.
2. Which concrete design ideas from those comparable systems should this
   project borrow? Explain where each idea would fit and what trade-off it adds.
3. Which functionality, safety property, recovery path, validation layer, or
   user experience is missing or weak in the current repository?
4. Prioritize the recommended changes. Separate observations verified from the
   repository from inferences or proposals, and call out any preliminary concern
   above that you believe is wrong or overstated.

Do not modify the repository. This is an advisory audit; Codex will independently
verify claims and decide what to accept, reject, or defer.

