# Pro review for checkpoint 0004

- Status: complete
- Reviewed C: [`763b456f2cc47cb8f088bcf0ca77c9c6318f631c`](https://github.com/sliortega295-ops/auto-research-skill/commit/763b456f2cc47cb8f088bcf0ca77c9c6318f631c)
- Handoff H: [`64c888708e9128f0f2c2ed5a1ec44eb68d7291ed`](https://github.com/sliortega295-ops/auto-research-skill/commit/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed)
- Branch/revisions read: H at [`64c8887`](https://github.com/sliortega295-ops/auto-research-skill/tree/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed), plus the later branch head [`ac13b157325d0e05167619901b25595363ea782f`](https://github.com/sliortega295-ops/auto-research-skill/commit/ac13b157325d0e05167619901b25595363ea782f) observed during writeback recovery
- Repository-grounded: yes
- External landscape checked: 2026-08-25
- Tests run by this reviewer: **NOT_RUN**. Test results below are either code-inspection findings or explicitly identified handoff-reported evidence.

## Evidence labels

- **[R] Repository-verified** — established by the exact repository contents, commit graph, or GitHub metadata at C/H.
- **[E] Externally verified** — established from a linked paper, official project, or current vendor documentation.
- **[I] Inference** — a reasoned conclusion from verified observations, not directly demonstrated.
- **[P] Proposal** — a recommended change, experiment, or policy; it has not been implemented or validated.

## Executive assessment

**[I] The project has a good protocol design inside a prototype implementation.** Its strongest idea is not a novel multi-agent loop. It is a narrow, versioned two-principal review protocol: Codex owns execution and adjudication, while a separate ChatGPT Pro conversation owns two advisory artifacts. GitHub commits make the review target and authorship inspectable. The `C/H/P/D` sequence is worth preserving.

**[R] The implementation is much smaller than the written operating contract.** The repository contains two skills, one 58.8 KB browser helper, one 9.8 KB local registry helper, and unit tests. It does **not** contain an executable auto-research coordinator that creates checkpoints, freezes a branch, emits a request identifier, acquires a lock, waits for `P`, verifies ancestry and path scope, persists recovery state, or records metrics. Those critical operations remain prose obligations in [`skills/auto-research/SKILL.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/skills/auto-research/SKILL.md) and [`references/github-handoff.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/skills/auto-research/references/github-handoff.md).

**Verdict:** not ready for unattended use on valuable software-development or paper-research repositories. It is suitable for a supervised single-user pilot only after the P0 controls in the paired plan are completed. The release blockers are structural: write isolation, durable recovery/concurrency control, exact request/reply attribution, private-output handling, missing tests for the live fallback added at C, and clarification of whether the browser automation is a permitted product surface.

| Dimension | Assessment | Basis |
|---|---|---|
| Architecture | Strong concept, incomplete runtime | **[R]** Clear role separation and durable Git state, but no coordinator/state machine |
| Implementation quality | Careful fail-closed utilities, uneven hardening | **[R]** Exact URL matching, atomic registry writes and confirmations are good; browser code has untested new paths, dead logic, repeated locators and fixed sleeps |
| Authority boundaries | Clear in prose, weak in enforcement | **[R]** Codex/Pro ownership is explicit; Pro currently has repository-wide write authority and the allowlist is checked only after a push |
| Safety | Not release-ready | **[R/E/I]** Same-branch contamination risk, prompt-injection exposure, private screenshot permissions, and current Terms uncertainty |
| Usability | Reasonable for its author, poor recovery UX | **[R]** Stable binding and short receipt are useful; there is no `doctor`, resume, status, rollback or one-command checkpoint flow |
| Software-project readiness | Supervised prototype | **[I]** Can support a careful audit experiment, not a long unattended project |
| Paper-research readiness | Earlier than software readiness | **[R/I]** No experiment/claim provenance schema, artifact hashes, dataset/config/seed contract, or rubric-based completion checks |

## 1. Repository-verified architecture and implementation

### 1.1 What is implemented

**[R] `auto-research` is currently a controller specification, not a controller program.** Its skill defines activation, standing permissions, consultation criteria, `C/H/P/D`, and completion semantics. Its only executable code is [`project_registry.py`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/skills/auto-research/scripts/project_registry.py), which maps one canonical GitHub origin to one local ChatGPT conversation.

**[R] `adspower-chatgpt` is the implemented interaction layer.** [`adspower_chatgpt.py`](https://github.com/sliortega295-ops/auto-research-skill/blob/763b456f2cc47cb8f088bcf0ca77c9c6318f631c/skills/adspower-chatgpt/scripts/adspower_chatgpt.py) discovers AdsPower/SunBrowser processes, speaks raw WebSocket/CDP, selects an exact page, inspects rendered state, selects a visible model label, drafts/sends text, waits for a new assistant count, captures screenshots, exports rendered conversation history, and opens a ChatGPT project in a background target.

**[R] C is the implementation under review.** C added the collapsed-project fallback, project-page wait, and failed-target cleanup. Comparing C to H shows that H is two commits ahead and changes checkpoint material only; the source and tests under review remain those at C. The complete request is in [`0004/handoff.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/.auto-research/checkpoints/0004-live-background-audit/handoff.md).

### 1.1a Live branch-drift observation

**[R] The branch-freeze invariant failed during this review.** After the first, incorrectly blocked webpage receipt, Codex advanced the branch from H through [`5173e9d`](https://github.com/sliortega295-ops/auto-research-skill/commit/5173e9d439d54492338bd25dc074c4efcb8c9e3a) and [`ac13b15`](https://github.com/sliortega295-ops/auto-research-skill/commit/ac13b157325d0e05167619901b25595363ea782f). The first recorded the blocked result in `decision.md`; the second changed source, tests and protocol documentation so `wait` has no default deadline. These commits are not part of C and are not silently treated as reviewed implementation.

**[I] This is direct evidence for the concurrency/recovery concern, not merely a hypothetical.** The protocol says local repository writes stop during review, but no lease or machine guard enforced it. An indefinitely blocking wait without a heartbeat, cancellation token or durable state also shifts failure from a visible timeout to a potentially unrecoverable hang. The paired plan therefore recommends an invocation lease, heartbeat, explicit cancellation and a separate response ref rather than relying on a raw unbounded wait.

### 1.2 Positive implementation properties

- **[R] Exact targeting and failure on ambiguity.** Conversation URLs are canonicalized and compared exactly; project links are canonicalized and deduplicated; ambiguous selectors fail.
- **[R] Foreground isolation is an explicit invariant.** `Target.createTarget` is called with `background: true`, and no `Target.activateTarget` call exists in the helper. A new project target reporting `visibility == "visible"` is rejected.
- **[R] Mutation has a confirmation boundary.** `open-project`, `select-model`, `new-chat`, `draft`, and `send` require `--confirm`.
- **[R] Several actions verify postconditions.** Model selection re-reads the visible label; send waits for a higher user-message count; wait requires both a higher assistant count and an idle page.
- **[R] The registry rejects embedded credentials, canonicalizes the origin, prevents one conversation from being bound to two repositories, uses an atomic rename, and sets `0700` on the parent and `0600` on the registry.**
- **[R] GitHub remains the declared authoritative response channel.** The full Pro response is not meant to be mirrored into a transcript, reducing duplicate durable state and privacy exposure.

These are meaningful strengths. They should be retained while reducing the amount of hand-maintained protocol around them.

### 1.3 Evidence quality

**[R] The handoff reports 12 AdsPower tests, 4 registry tests, validator success, installed-copy equality, one successful hidden live project open, and three failure cleanups.** This review preserves those as handoff-reported evidence; it does not claim to have rerun them.

**[R] GitHub exposes no status checks or workflow runs for C, and the repository has no checked-in CI workflow.** Therefore those results are not independently reproducible from GitHub alone.

**[R] C changed the project-opening implementation but did not add or modify tests.** The current [`test_adspower_chatgpt.py`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/skills/adspower-chatgpt/tests/test_adspower_chatgpt.py) tests direct project-link discovery and `create_background_target`, but not `click_exact_project`, `wait_for_project_page`, command-level cleanup, visible-target rejection, multiple/missing “Open project home” controls, or navigation to the wrong project. This is a release blocker because C's material behavior is concentrated in those untested paths.

## 2. Authority-boundary audit

### 2.1 `C/H/P/D`

| Stage | Assessment |
|---|---|
| `C` — reviewed implementation/evidence | **Keep.** It binds every audit claim to an immutable candidate rather than a moving branch. |
| `H` — Codex handoff | **Keep.** It records Codex's independent diagnosis, known failures, and exact request separately from the implementation. |
| `P` — Pro review/plan | **Keep, but isolate.** Separate authorship is valuable; direct mutation of the shared work branch is not. |
| `D` — Codex adjudication | **Keep.** It prevents advice from becoming executable authority and creates an explicit accepted/rejected/deferred record. |

**[I] Four stages are not excessive ceremony for consequential work, provided their metadata is generated and checked by a small state machine.** The ceremony becomes wasteful only because the same SHAs, statuses, allowlist, and instructions are currently copied manually across multiple Markdown files.

**[R/I] The current authorship boundary is semantic, not cryptographic.** The protocol names Codex-owned and Pro-owned artifacts, but it specifies no dedicated Pro bot identity, signed attestation, verified commit signature, or request-bound provenance record. A commit made through the user's GitHub connection may be attributed to the same account that owns the other stages. Preserve the logical stages, but do not claim Git metadata alone proves which model authored P.

**[P] Add one machine-readable checkpoint manifest and generate the repetitive headers.** The manifest should carry schema version, repository identity, branch, `C`, `H`, parent checkpoint, request ID, exact allowlist, expected response ref, phase, timestamps, validation state, and an adviser attestation or dedicated bot identity when available. Markdown remains the human record; the manifest becomes the recovery contract.

### 2.2 Two-file Pro write allowlist

**[R] The two files have a sensible semantic split:** [`pro-review.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/.auto-research/checkpoints/0004-live-background-audit/pro-review.md) holds findings and [`pro-plan.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/.auto-research/checkpoints/0004-live-background-audit/pro-plan.md) holds proposed next actions. Pre-creating them also makes absence distinguishable from an unexpected new path.

**[R] It is not an access-control boundary.** The current model-facing GitHub identity can write the repository broadly; file scope is an instruction followed by post-push inspection. If Pro changes source, the shared branch is already contaminated even when Codex correctly refuses to use the commit.

**[E] GitHub Agentic Workflows uses a stronger pattern: the agent runs read-only and requests structured “safe outputs”; separate scoped jobs validate and perform writes.** See [Security Architecture](https://github.github.com/gh-aw/introduction/architecture/) and [Safe Outputs](https://github.github.com/gh-aw/reference/safe-outputs/).

**[E] GitHub Apps can request `single_file_paths` for up to ten specified paths under the single-file permission.** See [GitHub App registration parameters](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-using-url-parameters). This is unusually well matched to the two-file contract, although per-checkpoint dynamic installation/configuration may add operational cost.

**[P] Prefer, in order:**
1. a read-only web adviser plus a deterministic write broker that accepts only a schema-validated review/plan payload;
2. a dedicated GitHub App constrained to the two checkpoint paths;
3. at minimum, an isolated response branch rooted at H, with Codex importing a validated P;
4. same-branch direct write only as an explicitly unsafe, trusted-single-user fast path.

### 2.3 Short webpage receipt

**[I] The short receipt is a good UI decision but a poor transaction signal.** It keeps the full audit in GitHub and avoids a second archive, but the helper does not parse or validate the four fields. More importantly, it attributes completion using page-idle state and message counts, so unrelated concurrent activity can look like the requested response.

**[P] Make GitHub the only machine completion signal.** Poll for a commit that carries the request ID, descends from the expected H/response ref, and changes only the allowlist. The receipt remains a human-visible acknowledgement. Add the request ID and H to it, or stop extracting it programmatically.

### 2.4 Direct same-branch writeback

**[I] Direct same-branch writeback is inappropriate as the default for valuable repositories.** Its advantage is low ceremony: P naturally descends from H and Codex can fast-forward. Its failure mode is worse than the saved ceremony: a malicious, mistaken, stale, or concurrent write lands on the shared work branch before validation. The observed H→`5173e9d`→`ac13b15` movement while P was pending demonstrates that the documented freeze is not enforceable.

**[P] Use a response branch created exactly at H**, for example `auto-research/pro/0004-<request-id>`. Require compare-and-swap creation/update, one atomic P commit, and no merge/rebase. Codex validates P, then cherry-picks or reconstructs the two-file commit onto the work branch. A PR is optional for human visibility; branch isolation supplies most of the safety without forcing review ceremony on every checkpoint.

### 2.5 Background CDP browser control

**[R] The background-target design is materially safer for desktop usability than foreground GUI automation.** It uses a stable URL, a dedicated target, no activation call, and a hidden-state postcondition. The handoff's live evidence specifically addresses active-window preservation.

The remaining risks are substantial:

- **[R] UI/DOM coupling.** Selectors and English labels such as `Open project home` are embedded in JavaScript strings and tied to current ChatGPT markup.
- **[R] Weak project-control scoping.** `click_exact_project` searches all rendered links/buttons for an exact first-line label rather than a semantically bounded project list.
- **[R] Timing brittleness.** Fixed 250 ms and 1 s sleeps coexist with polling; there is no navigation/event contract.
- **[R] Dead guard.** In `command_open_project`, the condition `not clicked.get("href") and clicked.get("action") != "open-project-home"` cannot hold for a successful `click_exact_project`, because that function always returns `action: "open-project-home"`. Navigation validation effectively occurs only in `wait_for_project_page`.
- **[R] Lifecycle leaks.** A successful task-created target has no owner record, lease, TTL, or close command. `create_background_target` can create a target and then time out before returning it, with no cleanup path.
- **[R] Cleanup can mask the primary error.** Error handling calls `close_target` while propagating an exception; a cleanup failure can replace the original diagnosis.
- **[R] Private screenshot mode is not hardened.** JSON exports are written atomically with `0600`, but `command_screenshot` uses `Path.write_bytes` without forcing `0600`; its parent directory also uses default permissions.
- **[R] Request attribution is count-based.** Send verifies only that the user-message count rose; wait verifies only a higher assistant count and idle state. It does not verify the exact sent content, message ID, request ID, or commit.
- **[R] Selector behavior and documentation are not fully aligned.** `choose_tab` resolves multiple matches to the sole visible tab when possible, while the skill broadly says ambiguous selectors fail closed. The stable-URL auto-research path normally avoids this, but the standalone contract should either document or remove the visible-tab fallback.
- **[R] Documentation terminology conflicts with implementation.** The skill says never use mouse/keyboard/keystrokes while the user works, while the helper uses background CDP `Input.insertText` and `Input.dispatchKeyEvent`. The intended rule appears to be “no physical/X11 foreground input”; it should say so.
- **[R] The helper owns a raw WebSocket implementation.** That removes dependencies but creates a large, security-sensitive transport surface with no protocol-level tests for fragmentation, oversized frames, disconnect/reconnect, or concurrent calls.

**[I] Replacing this immediately with Playwright would trade one risk for another.** The safer sequence is to first isolate transport, selector contract, and high-level actions; add fixture and fault-injection tests; only then compare the raw client with Playwright `connect_over_cdp` or another maintained CDP library.

### 2.6 Local repository-to-conversation binding

**[R] The binding's core identity choice is sound for the current single-user scope:** canonical `github.com/owner/repository` origin plus a stable `/c/` URL, with private local storage and no cookie or credential material.

Weaknesses:

- **[R] No lock.** `os.replace` makes each write atomic, but concurrent read-modify-write operations can lose updates.
- **[R] Coarse cardinality.** One conversation per repository cannot distinguish simultaneous branches, worktrees, or invocations.
- **[R] Fragile environment identity.** The browser environment is derived from the profile directory name before the first underscore, which can collide or change.
- **[R] No health check or repair UX.** There is no `doctor`, `unbind`, migration, stale-target diagnosis, or safe recovery flow.
- **[R] Conversation URL validation is permissive.** It requires `"/c/"` somewhere in the path rather than an explicitly supported path grammar.
- **[R] Durability is incomplete.** The file is fsynced before rename, but the parent directory is not fsynced afterward.
- **[R] Portability is limited by hard-coded `/tmp/lyy-experiments/...` roots** in both browser operation and tests.

**[P] Keep repository identity as the durable binding key, but add an invocation-scoped lease containing request ID, checkpoint, expected H, target identity, owner PID/start time, heartbeat, and expiry.** This solves concurrent attribution without multiplying permanent conversations.

## 3. Genuinely comparable systems and mechanisms worth borrowing

No single paper or project matches this repository exactly. The closest comparison is a composition of GitHub-native least-privilege workflows, durable workflow engines, software-agent interfaces, and autonomous-research evaluation systems.

| Comparable work | Mechanism compared directly with this repository | Concrete idea worth borrowing | Trade-off |
|---|---|---|---|
| [GitHub Agentic Workflows](https://github.github.com/gh-aw/) | Agent reads untrusted repository context but does not directly write; validated safe-output jobs perform scoped mutations | Put GitHub mutation behind a deterministic two-file write broker; validate schema, paths, secrets and request ID before write | Adds an Actions/job boundary and workflow maintenance |
| [GitHub Copilot cloud agent](https://docs.github.com/copilot/concepts/agents/cloud-agent/about-cloud-agent) | Uses an isolated ephemeral environment and works on a branch, optionally opening a PR | Give each Pro response an isolated branch rooted at H | One extra ref and cleanup policy |
| [Aider Git integration](https://aider.chat/docs/git.html) | Separates pre-existing dirty changes, auto-commits agent edits and supports explicit undo | Add dirty-tree preflight, actor-separated commits and one-command rollback/recovery | More commits and stricter repository hygiene |
| [SWE-agent](https://arxiv.org/abs/2405.15793) / [repository](https://github.com/SWE-agent/SWE-agent) | Shows that the agent-computer interface, commands and feedback shape reliability | Replace broad browser/Git abilities with a tiny adviser interface: read exact revisions, submit typed review/plan, report receipt | Less flexibility for ad-hoc browsing/actions |
| [Agentless](https://arxiv.org/abs/2407.01489) | Demonstrates that fixed localization–repair–validation stages can outperform a complex free-form agent loop | Keep a small deterministic checkpoint pipeline rather than growing a generic multi-agent framework | Less adaptability outside the intended workflow |
| [OpenHands SDK events](https://docs.openhands.dev/sdk/arch/events) / [persistence](https://docs.openhands.dev/sdk/guides/convo-persistence) | Uses typed immutable events and incremental persistent state for resumability | Add a compact append-only invocation journal and replayable phase state | Schema/versioning work; avoid importing the full SDK |
| [LangGraph persistence and interrupts](https://docs.langchain.com/oss/python/langgraph/persistence) | Thread-scoped checkpoints enable resume, fault tolerance and human approval | Model C→H→P-verified→D as explicit resumable states with idempotent nodes | A framework dependency is probably unnecessary; borrow the pattern |
| [Temporal retries/idempotency](https://docs.temporal.io/encyclopedia/retry-policies) | Separates deterministic workflow state from failure-prone activities and requires idempotent replay | Give send/write/poll operations idempotency keys and compensation rules; kill/restart-test every boundary | More state and failure taxonomy |
| [The AI Scientist](https://arxiv.org/abs/2408.06292) / [code](https://github.com/SakanaAI/AI-Scientist) | End-to-end idea, experiment, paper and simulated-review loop | Track claims, experiments and reviewer findings as linked artifacts instead of only prose handoffs | More metadata; automated self-review must not become authority |
| [MLAgentBench](https://arxiv.org/abs/2310.03302) / [code](https://github.com/snap-stanford/MLAgentBench) | Evaluates interpretable plans/actions against executable ML tasks and objective outcomes | Require an experiment contract, commands, metrics, seeds and success criteria before research execution | Up-front setup cost |
| [PaperBench](https://arxiv.org/abs/2504.01848) / [code](https://github.com/openai/preparedness/blob/main/project/paperbench/README.md) | Uses author-co-developed hierarchical rubrics with individually gradable tasks | Convert paper milestones and claims into hierarchical exit criteria, not “looks ready” prose | Rubric construction is labor-intensive |
| [Agent Laboratory](https://arxiv.org/abs/2501.04227) / [code](https://github.com/SamuelSchmidgall/AgentLaboratory) | Splits research into literature, experimentation and reporting phases with human feedback | Preserve deliberate review gates at phase boundaries while keeping Codex, not the reviewer, as executor | Longer latency and risk of ceremonial reviews |

**[I] The most valuable borrowing order is security first, durability second, research provenance third.** Adding more planner/critic agents would not address the current failure modes.

## 4. Missing or weak functionality

### 4.1 Recovery and concurrency

- **[R] No invocation lock, branch lease, heartbeat, expiry, or owner identity.**
- **[R] No idempotency key ties the browser request, GitHub P, receipt, and checkpoint together.**
- **[R] No durable phase state records whether the process stopped before send, after send, after P, during verification, or before D.**
- **[R] Recovery prose exists for divergence and false receipts, but no implementation or end-to-end tests exercise it.**
- **[P] Add a compare-and-swap state machine and a crash matrix covering every external side effect.**

### 4.2 Integrity and provenance

- **[R] P is not cryptographically or structurally bound to a request ID, C, H, model-visible identity, or source list.**
- **[R] The Markdown format asks Pro to name C/H, but there is no schema validation.**
- **[R] H's reported test evidence has no CI run, command log artifact, environment manifest, or artifact hash on GitHub.**
- **[P] Require a machine-readable provenance header and verify it before reading advice.**
- **[P] For research projects, add dataset/version, code SHA, environment, hardware, seed, exact command, metric definition, artifact digest and claim-to-evidence links.**

### 4.3 Validation

- **[R] Unit tests do not cover the material C fallback or its cleanup paths.**
- **[R] There is no disposable-repository + disposable-conversation end-to-end test.**
- **[R] There are no adversarial tests in which repository text attempts to expand the allowlist or induce source writes.**
- **[E] Indirect prompt injection is a demonstrated risk for tool-using agents; see [Greshake et al.](https://arxiv.org/abs/2302.12173) and [AgentDojo](https://arxiv.org/abs/2406.13352).**
- **[P] Add contract fixtures for UI selectors, fault injection for CDP/GitHub failures, and prompt-injection tests where the correct behavior is a blocked safe output.**

### 4.4 Safety and compliance

- **[R] The adviser consumes repository and webpage text as untrusted data while holding write-capable tools.** Prompt wording cannot make that equivalent to least privilege.
- **[R] Screenshots are not forced private.**
- **[R] Full DOM/body excerpts and rendered-conversation export broaden privacy and attack surface, even though auto-research declares them non-authoritative.**
- **[E] OpenAI's US Terms of Use effective January 1, 2026 state that users may not “automatically or programmatically extract data or Output.”** See [Terms of Use](https://openai.com/policies/row-terms-of-use/).
- **[I] The helper's DOM inspection, message export and automated receipt extraction create a material contract/compliance risk. This is not a legal conclusion, and a sanctioned feature, enterprise agreement, or explicit permission could change the result.**
- **[P] Do not release the browser path for sustained use until the permitted automation surface is confirmed. Prefer an official API/connector or make GitHub polling the machine channel and avoid programmatic extraction of ChatGPT output.**

### 4.5 Observability

- **[R] There is no structured log or metrics schema for consultation trigger, request ID, elapsed time, retries, browser target, GitHub ref, scope violations, accepted/rejected/deferred recommendations, cost, or defects caught.**
- **[P] Add a privacy-minimal event log and measure whether Pro consultation changes decisions or catches defects.** Without outcome data, the project cannot establish that its extra latency and ceremony improve work.

### 4.6 User experience

- **[R] There is no single `status`, `doctor`, `resume`, `abort`, `rollback`, `cleanup-targets`, or `scaffold-checkpoint` workflow.**
- **[R] Errors are emitted as JSON but do not carry stable error codes, request IDs, recovery instructions, or primary-versus-cleanup error chains.**
- **[P] Build the smallest useful CLI around the state machine, not a general agent framework.**

## 5. Removable redundancy and consolidation audit

The goal here is to remove duplicated sources of truth or unreachable control paths, not merely reduce line count.

| Candidate | Exact repository evidence | Recommendation | Regression risk | Required post-change validation |
|---|---|---|---|---|
| Duplicate model-control locator | `MODEL_STATE_JS` and `OPEN_MODEL_MENU_JS` in [`adspower_chatgpt.py`](https://github.com/sliortega295-ops/auto-research-skill/blob/763b456f2cc47cb8f088bcf0ca77c9c6318f631c/skills/adspower-chatgpt/scripts/adspower_chatgpt.py) repeat editor discovery, visible filtering, distance ranking and trigger selection | **Consolidate** into one selector contract returning the trigger and state; keep menu action separate | Medium: opening behavior or visible-label fallback may change | Fixture tests for present/missing/ambiguous controls, no-op selection, exact selection, and a live smoke against the bound page |
| Unreachable post-click guard | `command_open_project` tests `action != "open-project-home"` although every successful `click_exact_project` returns that action | **Delete and replace** with one explicit navigation postcondition inside `wait_for_project_page`, including expected project identity | Low; the current branch contributes no effective protection | Tests for success, no navigation, wrong project URL, hidden/visible state, and diagnostic preservation |
| Repeated manual checkpoint metadata | [`SKILL.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/skills/auto-research/SKILL.md), [`github-handoff.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/skills/auto-research/references/github-handoff.md), and every checkpoint repeat C/H/P/D, statuses, allowlist and receipt format | **Consolidate generation**, not historical files: one schema/manifest plus generated Markdown headers/templates | Medium: generator errors could corrupt the durable record | Golden-file tests, schema validation, ancestry/path invariant tests, and round-trip recovery from an existing checkpoint |
| Browser mechanics duplicated in controller policy | `auto-research/SKILL.md` contains target/model/send/wait details; `adspower-chatgpt/SKILL.md` contains auto-research receipt and GitHub protocol details | **Separate responsibilities**: controller owns authority/state; browser skill owns browser actions; a short interface contract is referenced by both | Medium: guidance may become fragmented | Scenario tests for activation, existing binding, new project, send, timeout, P verification, and final audit |
| Optional full transcript-export path | `EXPORT_CONVERSATION_JS`, `export_conversation`, CLI/docs/tests remain in `adspower-chatgpt`, while auto-research explicitly forbids using export as its response channel | **Move to an optional standalone module/skill**, or deprecate only if standalone export is not a product requirement | High for existing standalone users; low for auto-research | CLI compatibility/deprecation test and proof that the auto-research path imports/calls none of the export code |
| Repeated private-output path/mode logic | JSON output is hardened in `write_private_json`; screenshot output independently validates root and writes with default mode | **Consolidate** secure scratch-path validation and atomic `0600` byte/text writers | Low | Symlink/path-traversal, parent-mode, final-mode, interrupted-write and concurrent-write tests for JSON/PNG/prompt files |
| Hard-coded user-specific scratch roots | `/tmp/lyy-experiments/adspower-chatgpt` and `/tmp/lyy-experiments/auto-research/tests` appear in code/tests | **Replace** with a configurable secure runtime root and temporary test directories | Medium: migration and installed-copy assumptions | Default/override tests, path containment, multi-user permissions, cleanup, and no reference to the old absolute path |
| Raw WebSocket transport | `WebSocket` and `CDP` implement framing, masking, handshake and request dispatch in the single browser script | **Defer replacement.** First isolate behind an interface; then benchmark a maintained CDP client/Playwright against fault tests | High: browser compatibility and foreground behavior may regress | Transport contract tests, disconnect/reconnect, fragmentation, timeout, concurrent event traffic, no-activation assertion, and live parity run |

### Items that should **not** be deleted

- **[I] Do not collapse `C/H/P/D` into one commit.** Their distinct authorship and review targets materially improve provenance.
- **[I] Do not merge `pro-review.md` and `pro-plan.md` solely to save a file.** Findings and proposed action are different artifacts and support independent adjudication.
- **[I] Do not delete old checkpoints such as [`0001/web-review.md`](https://github.com/sliortega295-ops/auto-research-skill/blob/64c888708e9128f0f2c2ed5a1ec44eb68d7291ed/.auto-research/checkpoints/0001-initial-skill-audit/web-review.md).** They document protocol evolution. Treat them as historical records, not active compatibility code.
- **[I] Do not immediately deduplicate `canonical_conversation_url` across the two skills.** The duplication is small; a shared package would create a new cross-skill deployment dependency. Consolidate only after a stable package boundary exists.

## 6. Brittleness, coupling, testability and complexity

### Release blockers

1. **Same-branch, repo-wide write authority with post-hoc scope checking; branch drift has now occurred in the live checkpoint.**
2. **No durable state machine, invocation lock, idempotency key or branch compare-and-swap protocol.**
3. **No exact browser request/reply attribution and no concurrency protection.**
4. **Private screenshot permission defect and incomplete secure-output handling.**
5. **No tests for the material collapsed-project fallback and cleanup added at C.**
6. **No disposable end-to-end and crash/recovery test.**
7. **Prompt-injection exposure coupled to write-capable tools.**
8. **Unresolved OpenAI product/Terms compliance for programmatic webpage output extraction.**

### Deliberate trade-offs that are acceptable if explicit

- one dedicated conversation per repository;
- sparse consultations rather than review after every edit;
- GitHub as the sole durable shared source;
- C/H/P/D and separate review/plan artifacts;
- Linux + AdsPower/SunBrowser specificity for this user's environment;
- a visible `Pro` label stored as UI state, provided the system does not infer an unexposed internal model identifier.

### Optional cleanup

- replace the raw WebSocket implementation after behavior is covered;
- localize/i18n-enable ChatGPT selectors;
- add `unbind`, registry migration and stricter conversation path grammar;
- archive superseded checkpoints in the UI without rewriting Git history;
- expand portability beyond GitHub.com only after the current safety model is proven.

## 7. Readiness decision

**[I] Initial release decision: no for unattended real-project use; conditional yes for a narrowly supervised pilot.**

A pilot is reasonable only when all of the following are true:

- the repository is disposable or the Pro response is isolated from the work branch;
- the user actively supervises the invocation;
- browser use is confirmed permitted for the account/product context;
- screenshots and scratch artifacts are private;
- a request ID and exclusive lease prevent concurrent use;
- C's background fallback has direct tests;
- every P is atomically written, ancestry/path-verified, and easy to discard;
- the final result is not represented as complete when the audit is unavailable.

The project should resist becoming a general multi-agent platform. Its defensible scope is a **small, durable, least-privilege audit protocol for long-running software and paper research**, with Codex as executor and a separately grounded adviser whose output is imported only after deterministic validation.
