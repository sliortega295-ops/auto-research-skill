# Codex decision after Pro review 0004

- Status: complete
- Reviewed C: `763b456f2cc47cb8f088bcf0ca77c9c6318f631c`
- Handoff H: `64c888708e9128f0f2c2ed5a1ec44eb68d7291ed`
- Pro commit P: `e04edc2955471b44b564f0f049ec77f30123925a`
- P parent: `ac13b157325d0e05167619901b25595363ea782f`

## P verification

- The webpage became idle and reported the exact P SHA above.
- Fetch resolved the remote work-branch head to the same P.
- P is a single-parent commit and descends from H without a rewrite.
- P changes exactly the two allowlisted files in checkpoint 0004.
- Both files are non-empty, name the correct C and H, and preserve Pro's test
  status as `NOT_RUN`.
- P was committed through the user's GitHub identity, so its Pro authorship is
  established by the scoped workflow and receipt, not cryptographically by a
  distinct Git author or signature.

## Codex reassessment

The review is repository-grounded and materially useful. The project has a
sound narrow idea: Codex executes and adjudicates, Pro independently audits,
and C/H/P/D preserve immutable review targets. The current implementation is
nevertheless a supervised prototype. Most safety and recovery guarantees are
written instructions rather than executable invariants.

The observed branch movement needs a narrower interpretation than Pro gave it.
The first consultation had already returned a terminal blocked receipt before
Codex created `5173e9d` and `ac13b15`; those were not writes during an active
wait. However, the later manual recovery reused the old H while P was written
on top of `ac13b15`, without a new request ID or machine-checked expected head.
That still proves the recovery protocol is ambiguous and should be replaced by
an isolated response ref plus compare-and-swap verification.

The user explicitly requires no preset Pro timeout. An indefinite foreground
process is not the desired implementation, but the correction is a durable
waiting state with heartbeat, status, explicit cancellation, and resume. It is
not an implicit deadline.

[OpenAI's individual Terms of Use](https://openai.com/policies/terms-of-use/)
effective 2026-01-01 state that users may not automatically or programmatically
extract data or Output. The observed browser shows a personal-account context,
so automated DOM/output extraction is a real release and account-risk question.
This is not a legal conclusion. The project must record the uncertainty, avoid
representing the browser bridge as an officially supported surface, and obtain
authoritative clarification before unattended or distributed use.

## Dispositions

| Recommendation | Status | Evidence and reason |
|---|---|---|
| Preserve C/H/P/D and separate `pro-review.md` / `pro-plan.md` | accepted | The stages separate reviewed code, request, advice, and Codex authority. P demonstrated that the two-file split is useful. |
| Make an isolated response branch/ref the default P target | accepted | Same-branch post-hoc checking cannot prevent contamination. Start the response ref from a machine-recorded expected head and update it without force. |
| Add request ID, compare-and-swap ref checks, and exact P attribution | accepted | The blocked-then-resumed path reused H while the branch advanced, and page message counts cannot uniquely identify a request. |
| Put adviser writes behind a deterministic safe-output broker | accepted as target architecture | [GitHub Agentic Workflows](https://github.github.com/gh-aw/introduction/architecture/) independently demonstrates read-only agents plus separately validated writes. Implement the smallest local broker rather than importing the full framework. |
| Build a dedicated GitHub App with `single_file_paths` immediately | deferred | [GitHub supports up to ten scoped file paths](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-using-url-parameters), but checkpoint paths change and app provisioning adds operational work. First prove the response-branch broker. |
| Add a durable state machine, exclusive lease, idempotency, heartbeat, status, resume, abort, and recovery | accepted | These are currently prose-only invariants. The heartbeat/cancel path must retain the user's no-timeout rule. |
| Restore a preset wait timeout | rejected | The user explicitly requires unlimited Pro reasoning time. Liveness comes from durable state, heartbeat, and explicit cancellation. |
| Treat the earlier Codex commits as an active-review branch-freeze violation | rejected as stated | The first attempt had already terminated blocked. The recovery still exposed missing request/version attribution, which is accepted separately. |
| Make GitHub P the machine completion signal and keep the webpage receipt human-facing | accepted | A Git commit can be ancestry/path/request verified; page idle state and message counts cannot. |
| Resolve the ChatGPT browser-product compliance boundary before unattended release | accepted as an open release gate | Official individual Terms contain an automated extraction restriction. Exact applicability or an authorized exception requires authoritative clarification. |
| Harden screenshots, prompts, JSON, directories, symlink handling, and atomic private writes | accepted | `write_private_json` enforces `0600`, while `command_screenshot` currently uses ordinary `write_bytes` and default parent permissions. |
| Verify exact request content and manage task-created target ownership/cleanup | accepted | Current send/wait attribution is count-based, and successful background targets have no durable lease or TTL. |
| Add direct tests for the collapsed-project fallback, cleanup failures, wrong/visible targets, and a disposable adversarial E2E | accepted | Current tests cover link discovery and target creation but not the material fallback added at C. |
| Remove the unreachable post-click guard | accepted | A successful `click_exact_project` always returns `action: open-project-home`, so the condition cannot provide the intended navigation check. Replace it with a tested project-identity postcondition. |
| Consolidate duplicated selector and secure-output logic | accepted after regression fixtures | Duplication exists, but selector behavior is fragile; tests must precede consolidation. |
| Delete or disable transcript export now | deferred | Auto-research already forbids it. Standalone use was previously requested, so separate it from the controller before considering removal. |
| Replace the raw WebSocket/CDP client with Playwright immediately | deferred | That could regress the proven no-foreground-activation property. Isolate a transport interface and fault-test it first. |
| Make the scratch root configurable | accepted | A public skill should not hard-code a user-specific path. The installed local configuration may retain `/tmp/lyy-experiments` as its chosen runtime root. |
| Add a checkpoint manifest and generate repeated metadata | accepted | C/H/status/allowlist text is copied manually and has already drifted during recovery. Historical checkpoints remain immutable. |
| Add software and paper claim-to-evidence provenance | accepted | The intended research workflow needs exact commands, revisions, configs, data, seeds, hardware, metrics, digests, failures, and claim edges. |
| Add privacy-minimal event metrics and compare consultation value | deferred in full, minimal log accepted | Implement request/recovery events with P0; wait for a stable protocol and representative checkpoints before outcome claims. |
| Adopt LangGraph, Temporal, OpenHands, or another broad agent framework | rejected for now | Their persistence patterns are useful, but the project should remain a small deterministic controller. |
| Install Pro's proposed webpage system prompt verbatim | deferred | Its trust/capability guidance is useful, but its read-only/broker architecture conflicts with its direct-write instructions and its expected-head rule did not match this recovery. Revise after the response-ref contract is executable. |
| Readiness: supervised pilot only, not unattended valuable repositories | accepted | Write isolation, durable recovery, private outputs, exact attribution, and E2E validation are not yet implemented. |

## Next bounded plan

1. Add a machine-readable checkpoint manifest, request ID, and an executable
   verifier/coordinator with durable states, an exclusive lease, heartbeat,
   explicit cancel/resume, and stable failure codes. No implicit timeout.
2. Create a response ref from the recorded expected head and require one
   compare-and-swap P commit. Validate request ID, parent, exact path set,
   content size/encoding, pending markers, and secrets before importing it.
3. Harden the browser helper's private artifact writers, target ownership,
   primary-versus-cleanup errors, exact request attribution, and project
   navigation postcondition. Make its runtime root configurable while
   preserving the current local default.
4. Add contract/fault tests for every changed browser path and crash/recovery
   tests for every controller transition, followed by one disposable
   repository/conversation E2E that proves no foreground activation and no
   unvalidated work-branch mutation.
5. Revise the dedicated webpage system prompt against the executable response
   protocol, then install it only after the user approves changing project
   instructions.
6. Add research claim/evidence provenance and outcome metrics only after the
   P0 protocol gates pass.

## Remaining uncertainty or user authority required

- Authoritative clarification of the permitted ChatGPT webpage automation
  surface is required before claiming unattended or distributed readiness.
- Creating/installing a dedicated GitHub App or changing the ChatGPT project's
  persistent instructions requires separate user approval.
- No Pro-suggested source change has been implemented in this D commit.
