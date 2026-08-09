---
name: review-artifact-relay-and-state-barriers
description: "Operate credential-free exact-head reviewer lanes with ordered A/B/Auditor barriers, shared-account GitHub relay/readback, immutable artifact identity, and stable feedback-state verification."
version: 1.8.7
author: Hermes Agent
metadata:
  hermes:
    tags: [github, pull-requests, review, relay, exact-head, identity, race-conditions]
    related_skills: [autonomous-pr-prover, integration-audit-review, multi-agent-dev-workflow, github-operations]
---

# Review Artifact Relay and State Barriers

> **Real reviewer-CLI preflight:** Before moving from stubbed lanes to a live Codex/Claude CLI, load [`references/real-reviewer-cli-pilot.md`](references/real-reviewer-cli-pilot.md). It covers final-message isolation, scratch-artifact writes, explicit prompt/parser finding grammar, malformed-verdict retry limits, and semantic visual evidence.

## Purpose

Use this skill when independent reviewer processes must remain credential-free while default Hermes publishes their signed artifacts under a dedicated GitHub reviewer identity. It covers exact-head evidence sequencing, shared-account review-state hazards, artifact recovery, and false-success prevention.

This is a focused evidence-transport and review-state skill. Use `autonomous-pr-prover` for the full fix/re-review loop and `integration-audit-review` for the Auditor's substantive audit contract.

## Core invariants

1. Reviewer models receive no injected GitHub publication credential: remove token variables and route default `gh` lookup to a fresh empty run-owned config directory while preserving the model client's OAuth session. This is a trusted-lane environment boundary, **not same-UID capability isolation**; do not claim stored credentials are unreachable merely because default lookup fails.
2. Every artifact binds to one exact live PR head and one role/runtime signature.
3. Reviewer A uses formal GitHub review state; Reviewer B and the Integration Auditor use signed conversation comments when roles share one account.
4. A result counts only after default Hermes rechecks the live head, snapshots artifact IDs immediately before relay, relays under the verified reviewer identity, records the POST-returned immutable ID, and directly reads that exact ID back.
5. Author/signature/role/head text is public artifact shape, not ownership or relay-attribution proof. Never let a pre-relay reviewer-side artifact satisfy transport merely because its body matches.
6. Human feedback from a shared publishing login remains human unless its exact immutable ID is positively known as run-owned.
7. A terminal `merge-ready` result requires a stable observation of all feedback surfaces, not merely an unchanged code head.
8. When the contract declares Reviewer A → Reviewer B → Integration Auditor, each prior artifact must be relayed/read back before the next lane's packet is frozen. Do not parallelize A/B under an ordered lifecycle.
9. Prepared artifact paths are run-scoped evidence slots: prove each path is absent before launch, or use a unique run/head/role path. Never let a reviewer silently inherit an old artifact from another PR, head, role, or attempt.
10. The relay identity is a verified per-process execution context, not a remembered token source. Resolve the configured isolated reviewer profile or credential, smoke-test `gh api user`, and fail closed before any POST if the login is not the expected reviewer. An environment variable named for a reviewer is not identity proof: when multiple `gh` keyring accounts exist, unset inherited `GH_TOKEN`/`GITHUB_TOKEN`, resolve the expected `--user` explicitly, then run `GH_TOKEN="$resolved_token" gh api user` and compare the login before using that same process-scoped token for relay. Never switch the global active account or print the token.
11. A frozen packet is a validator boundary, not an informal JSON dump: use exact scalar types (reject boolean-as-integer), require every promised surface and its completeness/count/item invariants, and include the PR plus trusted governing issue bodies when the reviewer mandate requires them.
12. Human-readable reviewer prose is not canonical artifact proof. Run the repository's shipped artifact parser against the exact prepared body before relay and against the exact immutable-ID GitHub readback afterward; verify parsed role/head/status/blocker/runtime/adversarial declarations, not substring presence alone.
13. Parser redaction is not publication redaction. Treat the child-produced body/path as raw local evidence; sanitize the entire body into a unique relay-eligible copy **before** the external POST, parse and validate that sanitized copy, relay only it, then require the immutable-ID API body to equal the exact sanitized bytes before rechecking parsed finding parity. Never compare two post-publication scrubbed representations and call the raw publication safe.
14. Finding parity is record-exact, not ID-only. The lane's final message and prepared artifact must carry the same finding ID, severity, and one-line summary; paraphrasing the same finding in one surface is a transport failure. Never hand-edit a reviewer-owned artifact to repair parity—rerun only that role on the unchanged packet/head with an explicit byte-identical `FINDING:` requirement.
15. A completion watcher or wrapper exit proves only process termination. Before accepting any builder, reviewer, relay, or prover result, read the authoritative stdout/JSON, stderr, state journal, exact local/remote/live head, worktree cleanliness, and immutable GitHub readback. An argv/config rejection before the trusted lane starts is not a consumed repair cycle, but this must be proved from the absence of lane execution and side effects.
16. If a terminal transport-only stop is recovered into a complete triad that finds blockers, preserve the remaining repair count explicitly. Freeze the deduplicated ledger with shipped parser/classifier types, invoke only the one remaining shipped builder cycle, verify its parser/push/comment readback, acknowledge only the recovered run-owned immutable IDs, and re-enter through a fresh final-verifier state seeded at `MAX_ATTEMPTS`. Never edit the terminal journal or reset the attempt budget to gain another fix cycle; see `references/terminal-prover-reentry-after-recovered-triad.md`.
17. A high-level GitHub CLI mutator exiting zero is not publication proof. For reviewer relays, prefer direct REST POSTs that return an immutable review/comment ID, then read that exact ID back and compare author, head/type, raw bytes, and parser output. If a zero-exit relay leaves no artifact, classify transport failure, inspect the actual process-scoped identity and target, and do not consume a builder cycle. See `references/direct-github-review-relay.md`.
18. Before spending another expensive reviewer run after a transport-only stop, instrument the relay to retain the exact prepared artifact plus HTTP status/response metadata. If the orchestrated relay still leaves no response file, manually invoke the same relay with that retained real artifact and explicit repo/PR/head, capture/read back the immutable ID, and continue through the documented lower-level ordered recovery. Never post a synthetic transport-test review or reconstruct a verdict from a summary. Also report execution state literally: configured/preparing/paused is not running; verify a tracked process or live PID before saying a goal is active.
19. A final auditor result is not complete when it exists only in the originating Buzz/channel thread. Relay the prepared artifact onto the PR itself as a conversation comment, then read back that exact immutable PR artifact and bind it to the audited head. A channel post may summarize or link the result, but it is not a substitute for the PR-surface artifact. If PR relay/readback is unavailable, classify transport/evidence as blocked and do not imply that the PR was posted or certified.
20. A publisher-authored feedback acknowledgement is authorized only by an exact immutable-ID/body-evidence pin. The report's displayed unresolved array is bounded evidence, not necessarily the full set. When replacing a pin, run the shipped reconciliation over the live surfaces with retained `verified_artifacts` and **no operator pins**, build one cumulative pure acknowledgement for that complete unresolved set, then simulate the proposed later pinned post and require zero unresolved before publication. This no-pin baseline is necessary because removing an old pin can revive both its cleared targets and the old bookkeeping post itself. A feedback-only stop must preserve the state journal: do **not** use a broad reset that deletes `verified_artifacts`, because previously run-owned reviewer comments then re-enter feedback and each replay can create another acknowledgement cycle. If ownership state was already lost, recover only from exact immutable GitHub artifacts whose role/head/verdict/signature/body digest are independently revalidated, then use a deterministic exact-artifact replay while keeping normal gates, relay/readback, and final feedback reconciliation. Preserve exhausted repair budgets so a review-only replay cannot silently regain a builder. For credential-bearing request paths, adversarial review must include parser-accepted header-invalid sentinels and prove raw native request errors cannot expose the value even when transport never starts. See `references/feedback-replay-and-credential-errors.md`.
21. Background completion is a human-visible state barrier. `notify_on_complete` proves termination, not communication: immediately read authoritative output/state, recheck the live head, and publish the resulting Buzz milestone before unrelated work. Keep detailed evidence in the originating thread, but publish channel-root start/blocker/push/gates/review/final milestones. Never say reviewers are running without a currently active tracked process. If a factual `needs-Karan` item blocks valid code repairs, resolve the fact from the direct source and route only demonstrated blockers through the remaining bounded builder cycle; never bypass a genuine human decision or restore spent repair budget. See `references/completion-and-channel-milestone-barriers.md`.
22. Hash publication is a terminal artifact-finalization barrier. Never publish a manifest/report hash while the prover or another gate can still rewrite that path. Evidence-producing gates must use immutable run-scoped output directories, or a later prover gate must consume the finalized directory read-only. After the last writer exits, verify the closed file set, child hashes/sizes/media dimensions, report head/base/outcome, and live PR head; only then hash, publish, read back, and freeze reviewer packets. If a conversation comment raced a later rewrite, correct that comment in place with an explicit audit note, verify exact-ID body readback, and require a fresh audit. See `references/artifact-finalization-before-hash-publication.md`.

## Ordered lifecycle

For a prepared Integration Auditor conversation-comment artifact, use `scripts/publish_integration_artifact.py`: preflight without `--publish`, then publish only after exact-head and reviewer-identity checks pass. The script deduplicates exact bodies and verifies immutable-ID readback byte-for-byte.

```text
exact-head gates + real installed adapter smoke
→ launch Reviewer A in a separate clean detached worktree
→ validate raw A → sanitize a unique relay-eligible A copy → parse sanitized A → immediate pre-relay ID snapshot → relay sanitized formal state → read back returned ID and compare exact sanitized bytes
→ refresh packet with live A artifact
→ launch Reviewer B in its own clean detached worktree
→ validate raw B → sanitize a unique relay-eligible B copy → parse sanitized B → immediate pre-relay ID snapshot → relay sanitized signed comment → read back returned ID and compare exact sanitized bytes
→ refresh reviews/comments/threads/checks into a post-A/B packet
→ launch Integration Auditor against that refreshed packet
→ validate raw Auditor body → sanitize/parse its relay-eligible copy → immediate pre-relay ID snapshot → relay sanitized body → direct returned-ID readback and exact-byte comparison
→ default-Hermes synthesis
```

Use this strict sequence whenever the contract names Reviewer A → Reviewer B → Integration Auditor or later lanes adjudicate earlier artifacts. A/B concurrency is allowed only when the governing contract explicitly declares them independent and default Hermes discloses that the run is not proving an ordered lifecycle. The Auditor is always a serialization barrier when it certifies A/B state. Missing not-yet-produced artifacts are `review-state pending`, never a clean review set.

## Parent iteration-budget barrier

Treat the parent agent's remaining tool-call/turn budget as a launch prerequisite, not an afterthought. Before starting a long builder or the ordered review chain, reserve enough parent operations for the complete next durable barrier:

- live-head and feedback refresh;
- packet/worktree freeze and integrity checks;
- child launch plus completion notification;
- raw artifact validation, sanitization, parser preflight, relay, immutable-ID readback, and packet refresh;
- every still-required downstream lane;
- final two-read feedback stability, tracker update, and user-facing closeout.

A healthy bounded background process with `notify_on_complete` should not be polled every minute. Allow at most one diagnostic process-tree or worktree-status inspection unless a concrete stall signal appears; otherwise rely on completion notification and preserve the iterations for exact-head review and transport proof.

If the available budget cannot reach the next complete durable barrier, do not launch the expensive lane. Write a self-contained checkpoint containing the exact head, process state, completed gates, pending lane, worktree/packet/artifact paths, cycle budget, and authority boundaries. After a builder opens a PR, exact-head preflight is a valid checkpoint; it is not review completion. If a hard iteration ceiling arrives before A → B → Auditor finishes, report the chain as pending and never compress missing reviewer evidence into `merge-ready`.

## Exact runtime entitlement smoke

Before launching multiple expensive reviewer lanes, run one zero-tool, one-line smoke through the **exact** reviewer CLI, account/auth context, model, reasoning setting, config-isolation flags, sandbox mode, and output-artifact path shape. A model named in an old prompt or prior run is not proof that the current account can still invoke it.

If the smoke fails before substantive review begins:

1. classify it as launcher/runtime preflight, not a consumed review or repair cycle;
2. prove the prepared artifact path is absent and each detached worktree remains clean at the assigned head;
3. inspect the account's current configured/supported runtime, then smoke that exact runtime once;
4. update every prompt declaration, signature, parser expectation, and launcher pin before relaunching;
5. preserve the original packet/head when its hashes remain valid—do not regenerate evidence merely because runtime entitlement changed.

Never fan out A/B/Auditor with an unproven model pin. One cheap exact-context smoke prevents duplicated provider rejections and ambiguous partial artifacts.

## Reviewer launcher write-mode gate

Choose the launcher mode from the evidence contract **before** starting the child:

1. Inspect the actual wrapper/`--help`; do not assume Codex and Hermes reviewer wrappers accept the same flags.
2. If a Codex A/B lane must run temp-directory/cache-producing tests or materialize its signed body under `/tmp`, use its bounded workspace-write mode in a disposable detached worktree. The prompt still forbids repository edits and allows only `/tmp` evidence; recheck `git status` after exit.
3. Use Codex read-only mode only when all required probes are genuinely write-free and an inline prepared body is acceptable. Do not ask a read-only sandbox to promise an on-disk `/tmp` artifact and then treat the denied write as a product/review failure.
4. The hardened Hermes Integration Auditor wrapper may already enforce `HERMES_WRITE_SAFE_ROOT=/tmp` and may not accept Codex sandbox flags. Invoke its native interface without invented `--workspace-write`/`--read-only` flags.
5. Treat temp-directory, `__pycache__`, or compile-cache failures caused solely by a read-only reviewer sandbox as infrastructure evidence. Rerun in the bounded write mode or use an in-memory syntax probe; never convert them into PR blockers.

See `references/reviewer-launcher-write-modes.md` for the capability matrix, command shapes, recovery path, and cleanliness checks.

## GitHub credential isolation and relay attribution

Unsetting `GH_TOKEN` alone is insufficient on hosts where `gh` resolves OAuth from its config profile and OS keychain. Preserve the model client's required session environment, but give the reviewer a fresh empty run-owned `GH_CONFIG_DIR`, unset all GitHub token variables, and provide a frozen evidence packet so the prompt never requires authenticated live `gh`. Negatively smoke-test that default `gh api user` fails in the exact reviewer environment without printing credential material. Treat this as default-route denial for a trusted lane—not proof that a same-UID child cannot unset `GH_CONFIG_DIR` and rediscover the operator profile through real `HOME`. If the governing contract requires credentials to be genuinely unreachable, stop for an approved profile/OS isolation design instead of overclaiming the environment transform.

After the reviewer exits, take a new artifact-ID snapshot immediately before relay. Prefer the immutable ID returned by the relay POST and read that exact artifact back. If transport cannot return an ID, require exactly one matching new ID since the immediate pre-relay snapshot. A reviewer-side post, copied body, old matching artifact, no-op relay, or ambiguous pair of new IDs must fail closed rather than count as `published`/`read_back`.

See `references/stored-gh-credentials-and-relay-attribution.md` for the credential-resolution paths, launch contract, relay barrier, and deterministic regressions.

## Pre-launch artifact namespace hygiene

Prepared review bodies are evidence, not scratch files. Before every reviewer launch:

1. derive an artifact path that includes the PR, exact head or run ID, and role;
2. assert the path does not already exist, or archive/remove the old file in the parent before launch;
3. record the expected path in the immutable packet and child prompt;
4. after exit, validate that the artifact was created during the current process window and contains only the current PR/head/role;
5. reject any stale PR number, SHA, role, runtime, verdict, or copied `DONE:` marker before relay.

Static paths such as `/tmp/reviewer-a-body.md` are acceptable only when the parent proves absence before launch. A child rewriting a stale artifact into the correct shape is not proof that the path was clean; the pre-launch absence check is the barrier.

## Prompt-schema preflight before an expensive reviewer launch

Artifact parser requirements must appear in the reviewer prompt itself, not only in the parent operator's checklist. Before launching A, B, or the Auditor, preflight the prompt and require it to name the exact prepared path plus every shipped standalone declaration:

```text
ROLE=<configured-role>
RUNTIME=<pinned-model/reasoning>
HEAD=<full-exact-sha>
STATUS=pass|fail
BLOCKING=<plain integer>
KILL-SWITCH: <non-empty adversarial attempt and result>
```

Also require the human-readable reviewer signature and final `DONE:` marker. A prompt that merely asks for “head, blocker count, checks, and signature” is insufficient: a reviewer can perform a complete substantive audit yet produce a parser-invalid artifact, forcing an expensive same-head correction run before anything may be relayed.

Parent preflight should therefore verify, before process launch:

1. the unique run/head/role artifact path is absent;
2. the prompt names the exact role/runtime/head and artifact path;
3. the prompt contains all canonical declaration keys and says each must appear exactly once;
4. the final marker verdict/count/head must agree with the declaration block;
5. the correct launcher write mode is selected for the promised `/tmp` artifact and probes.

If a completed substantive review still omits declarations, preserve its findings, run one narrow same-head transport-shape correction for the same role, parser-preflight the corrected body, and only then relay. Do not consume a builder cycle, run the next ordered reviewer, or hand-edit the reviewer verdict into compliance.

## Artifact recovery

A hardened read-only reviewer may complete successfully but be unable to write its requested `/tmp` body. Prefer choosing the correct bounded write mode up front when the artifact is required. If the lane already ran read-only, recover the exact fenced artifact from final stdout in the parent process. If stdout contains only a summary/final marker and not the complete artifact body, do **not** reconstruct or paraphrase the body in the parent: rerun only that role once against the unchanged packet and exact head with its bounded workspace-write mode, require `/tmp`-only evidence writes, and verify the disposable repository worktree remains clean. The latest complete same-head reviewer result governs.

Recovery produces the **raw child artifact**, not permission to publish those bytes. Before relay, sanitize the complete body into a new run/head/role-bound file, preserve the raw file as local evidence, and run the canonical parser against the sanitized copy. Relay commands must receive the sanitized path only. After POST, compare the immutable-ID API body's raw bytes with that sanitized file before applying parser normalization. See `references/pre-publication-redaction-and-relay-proof.md`.

Then validate:

- required prefix;
- exactly one standalone role line;
- exactly one canonical full `HEAD=<sha>` line;
- one reviewer signature and pinned runtime line;
- verdict and blocker count agree with the final machine marker;
- required standalone adversarial declarations (for example a line beginning exactly `KILL-SWITCH:`) are present when the shipped parser requires them;
- the exact recovered body passes the repository's shipped parser under the supported runtime(s), with parsed role/head/status/blocker values matching the lane contract;
- no code fences, token counters, or surrounding explanation were copied into the relay body.

After relay, fetch the immutable-ID GitHub artifact and run the same parser against that fetched body. Compare the sanitized relay-eligible file text with the raw API body before trimming either side: GitHub may preserve the file's final newline, and asymmetric `rstrip()` creates a false mismatch that can trigger a duplicate relay. The raw child artifact is deliberately **not** the publication comparison target. Local parser success does not prove GitHub readback validity. If a same-head artifact is semantically sound but parser-invalid, preserve the failed downstream audit, rerun only the affected role with explicit canonical declarations, parser-preflight it, sanitize the corrected body, relay/read back, refresh the packet, and rerun dependent downstream lanes. Do not consume a builder cycle or invalidate independently valid same-head upstream artifacts when no code changed.

A same-head transport correction is still a fresh substantive audit, not a mechanical reformat. Its blocker count may legitimately differ because the new reviewer run can deduplicate, reproduce, or refute findings differently. Never force the prior malformed count into the corrected artifact and never union two same-role attempts as if they were independent lanes; the latest complete parser-valid exact-head audit governs, while the malformed attempt remains transport evidence.

Re-query the head before relaying. If a compound POST command returns a concrete URL/immutable ID and then exits non-zero, assume the side effect may already be live: do **not** retry the POST. Fetch that exact ID in a separate read-only command, compare the API body to the sanitized publication bytes, and rerun only the local verifier. Keep Unicode accounting straight: character length is not file byte size; compare exact UTF-8 text plus SHA-256/encoded byte counts, never `len(str)` against `stat`, and never use asymmetric trimming. See `references/unicode-safe-post-readback-barrier.md`.

## Stable feedback-state gate

Sequential reads of conversation comments, formal reviews, inline comments, and review threads can miss feedback arriving between surfaces while the PR head remains unchanged. Before a terminal success:

1. record immutable IDs and relevant state from every feedback surface;
2. classify feedback;
3. re-read immediately before reporting;
4. fail closed or retry when any surface changed.

Keep this bounded and workflow-specific; do not build a generic snapshot platform.

## Verification checklist

- [ ] local/remote/live head agree;
- [ ] prepared artifact path is run-scoped and proven absent before launch;
- [ ] reviewer environment preserves model auth but routes `gh` to a fresh empty config and negatively proves `gh api user` cannot authenticate;
- [ ] reviewer runtime and role pin verified;
- [ ] artifact shape, creation window, current PR/head/role, and blocker count validated;
- [ ] exact prepared body passes the shipped canonical artifact parser, including required standalone adversarial declarations, and parsed claims agree with the final machine marker;
- [ ] the complete raw child artifact is sanitized into a unique relay-eligible copy before publication; the sanitized copy preserves required grammar/signatures, contains no synthetic-secret sentinel in a normal-loop regression, and is the only path rendered into relay argv;
- [ ] for publication-redaction changes, a one-seam source mutation in a fresh disposable exact-head worktree makes the narrow suite fail, the complete captured failure output contains zero synthetic-sentinel occurrences, and the primary worktree is clean after probe cleanup;
- [ ] live head unchanged immediately before relay;
- [ ] immediate pre-relay artifact-ID snapshot recorded after reviewer exit;
- [ ] relay execution context smoke-tests as the expected reviewer without switching global identity;
- [ ] the POST-returned immutable ID—not merely a matching body—is read back and verified for author/type/commit or canonical head/role/verdict;
- [ ] immutable-ID API body equals the exact sanitized publication bytes/digest before trimming or parser normalization;
- [ ] the exact immutable-ID GitHub body also passes the shipped parser with the same role/head/status/blocker/finding claim as the sanitized prepared body;
- [ ] A → readback → B → readback → Auditor packet ordering preserved when the contract is ordered;
- [ ] shared-login human-collision probes remain blocked;
- [ ] feedback-arrival-between-reads probe fails closed;
- [ ] no merge authority inferred from reviewer pass.

## Pitfalls

- Do not equate “token variables unset” or “default `gh` lookup denied” with OS-level credential isolation. A same-UID child that preserves real `HOME` may restore the operator profile by unsetting `GH_CONFIG_DIR`; state the trusted-lane boundary precisely and require separate approval if genuine unreachability is needed.
- Do not accept a packet because it parses and its repo/head strings match. Reject boolean-as-integer versions/sequences, missing required surfaces, malformed completeness/read method/count/items, count mismatches, missing/null API fields, wrong lane bindings, and omitted PR/governing-issue bodies required by the reviewer mandate.
- Do not ask a credential-free reviewer to inspect live private GitHub state with `gh`; give it the frozen packet and keep live readback in the parent.
- Do not use a snapshot taken before reviewer launch as relay attribution. Snapshot immediately before relay and bind transport to the POST-returned ID; a no-op relay must never inherit a reviewer-side post.
- Do not parallelize A/B when the governing contract declares an ordered A → B → Auditor lifecycle; relay/read back each stage before freezing the next packet.
- When augmenting or regenerating a packet after A or B relay, refresh `generated_at` from the new freeze operation. Validate that it is not earlier than any newly included artifact timestamp; a post-A packet with a pre-A timestamp is internally contradictory even when its bytes contain A.
- Do not parallelize the Integration Auditor with A/B when it must certify their live artifacts.
- Do not reuse a prepared-artifact path without proving it is absent before launch; stale files can carry an old PR, head, verdict, or signature into a new lane.
- Do not treat a remembered Keychain/PAT lookup—or a reviewer-labeled environment variable—as the reviewer identity. A token variable can silently hold the active operator/PR-author credential. Resolve the expected account explicitly in the relay process, smoke-test the exact token with `gh api user`, and stop before mutation on mismatch. If relay exits zero but immutable readback finds no artifact, classify transport failure and inspect live reviews plus actual relay identity before retrying; do not consume a product repair cycle when the head did not change.
- Do not repeatedly rerun a costly reviewer while the publication path is still opaque. Preserve the first parser-valid exact-head artifact, make the relay retain response/status diagnostics, and test the corrected transport with that real artifact. If direct manual relay succeeds while the orchestrated call leaves no response file, recover the ordered chain through the lower-level transport procedure rather than claiming the reviewer must run again. Never publish a fake transport-preflight review.
- Do not describe a configured stage as an active process. Check the process table/handle immediately before status updates; say prepared, paused, or awaiting launch when no reviewer is actually running.
- Before launching a final review/fix chain, reserve enough execution budget for builder completion, exact-head verification, A/B completion and relay/readback, a refreshed post-A/B packet, Integration completion and relay/readback, and authorized closeout. If that chain cannot fit, stop at a stable checkpoint before launching the next expensive lane rather than ending one gate short.
- Do not burn the parent control-plane budget by repeatedly polling healthy quiet reviewer jobs. Launch with completion notification, use one bounded diagnostic status check only when needed, and preserve enough iterations for artifact validation, relay/readback, the post-A/B Auditor barrier, and final stable-state reconciliation.
- Treat one reviewer-only gate failure as pending evidence until it is reproduced and localized. Re-run the focused test in the same launcher mode and an independently verified exact-head environment; classify product defect, reviewer-infrastructure limitation, or flake explicitly instead of either promoting or dismissing it from one run.
- Temporary probes are exact-head artifacts. Before rerunning one after a head/worktree change, inspect its embedded `ROOT`/`PYTHONPATH`/SHA and verify it imports the current reviewed checkout. Never cite output from a stale detached worktree as evidence for the new head.
- If a fix makes an unchanged former-red probe stop at a newly expected fail-closed exception, run both: (a) the exact probe, disclosing the expected non-zero exit, and (b) a separately diffed observation copy that adds only the minimal exception catch needed to print later observables. Back both with shipped assertion-based regressions.
- A reviewer-process/provider interruption after evidence gathering is an incomplete lane, not a product verdict. Preserve the exact head, recover durable `/tmp` evidence, and retry with a narrower prompt for the same frozen question without weakening model, identity, or contract gates. A reported usage-reset timestamp is a checkpoint, not immutable truth: if Karan says the subscription was manually reset, cancel any scheduled delayed retry, re-query the live head, and immediately retry the hardened lane. Remove the redundant scheduled job first so it cannot later duplicate review or tracker mutations.
- Do not treat a missing `/tmp` body as review failure when complete signed stdout exists.
- Do not use `PR-PROVER: ACKNOWLEDGED <id>` bookkeeping to resolve a formal `CHANGES_REQUESTED` review. Formal reviews have native GitHub resolution state: clear a stale old-head review with an explicitly evidenced GitHub dismissal, or with a later decisive review that the feedback classifier is allowed to treat as human resolution. A run-owned exact-head approval may be correctly excluded as lane evidence and therefore may not clear an older non-owned change request. If an ineffective ACK comment was already published, it becomes unresolved prose itself; after resolving the formal review natively, clear that comment with a separate valid pure ACK and verify both immutable IDs/readbacks before terminal reconciliation.
- Do not exclude a whole reviewer login from human-feedback checks.
- Do not reconstruct run ownership from copyable body fields.
- Do not trust a POST's printed JSON without independent readback when the command exited non-zero.
- Do not let green unit tests override a real installed-adapter false-success reproduction.
- Do not equate a successful live `--output-last-message` smoke with proof that the reviewer can write its prompted artifact. The CLI may own the final-message file outside the model sandbox; separately prove the exact run-scoped artifact path is writable through the shipped adapter while the exact-head worktree remains clean.
- Do not accept a final-message transport patch until the real adapter argv still preserves every contract-required launcher setting: ephemeral/noninteractive mode, model and reasoning pin, config/rules isolation, sandbox, explicit artifact-directory access, credential stripping, and original exit status.
- Do not accept semantically adversarial prose as a canonical reviewer artifact without running the shipped parser. A bullet headed “Adversarial checks” may still fail a contract that requires a standalone `KILL-SWITCH:` line. When this is the only failure at an unchanged head, treat it as a transport-only same-head correction: preserve the failed audit, rerun the affected role, parser-preflight before and after relay, then rerun dependent downstream lanes—no builder or push.
- Do not mistake parser-level scrubbing for publication safety. If `read_prepared()` returns a scrubbed finding while the relay still receives the original artifact path, the public POST can leak the raw value and later appear valid because readback scrubs it again. Sanitize before publication, relay only the sanitized copy, and prove the remote received those exact bytes.

## References

- `references/completion-and-channel-milestone-barriers.md` — treat background completion as an immediate state/readback barrier, publish channel-root Buzz milestones while keeping evidence in threads, enforce artifact/final-verdict finding parity, and resolve factual `needs-Karan` items without bypassing human judgment or repair budgets.
- `references/feedback-replay-and-credential-errors.md` — reconcile publisher-authored feedback from a live no-pin baseline when replacing exact-post pins, simulate cumulative ACK bodies to zero unresolved before publication, preserve review-only attempt caps, and probe credential leaks through native header-validation errors before transport.
- `references/direct-github-review-relay.md` — resolve and verify the exact reviewer identity, publish formal reviews/comments through direct REST POSTs that return immutable IDs, and recover safely when a zero-exit relay creates no artifact.
- `references/manual-lower-level-triad-recovery.md` — recover an ordered A → B → Auditor chain after a terminal transport-only prover stop: detached-wrapper watchdogs, same-head parser correction, sanitized relay/readback, and shipped packet refreeze without editing terminal state or consuming a builder cycle.
- `references/terminal-prover-reentry-after-recovered-triad.md` — when that recovered triad finds blockers and one cycle remains, freeze the deduplicated ledger with shipped types, verify the final builder push/comment, acknowledge only proven run-owned artifacts, and launch a fresh exact-head verifier with the attempt cap preserved rather than reset.
- `references/pre-publication-redaction-and-relay-proof.md` — distinguish parser normalization from publication safety; sanitize the complete artifact before POST, relay only the sanitized copy, compare immutable-ID readback to exact sanitized bytes, and mutation-prove the normal loop never publishes a synthetic secret sentinel.
- `references/unicode-safe-post-readback-barrier.md` — prevent duplicate relays after a compound-command failure; capture the POST ID, read back that exact artifact, and compare Unicode-safe UTF-8 bytes/digests rather than character counts or trimmed text.
- `references/real-reviewer-cli-pilot.md` — normalize real CLI diagnostics away from parseable verdicts, align scratch writes and prompt/parser finding grammar, honor malformed-verdict retry budgets, and require semantic mobile/print evidence.
- `references/canonical-artifact-parser-preflight.md` — prepared-body and immutable-ID GitHub parser preflight, exact final-message/prepared-artifact finding parity, reviewer-owned same-head rerun recovery without hand-editing or consuming a builder cycle, and read-only probe evidence handling.

- `references/frozen-packet-validation-and-trust-boundary.md` — strict packet schemas and task-contract bodies, boolean-as-integer fail-open probes, precise default-route versus same-UID credential semantics, two-snapshot relay attribution, and persistent-shell `GH_CONFIG_DIR` hygiene.
- `references/background-review-budget-and-flake-triage.md` — preserve parent iteration/runtime budget across long A/B jobs, distinguish termination from authoritative outcome, adjudicate unchanged timing flakes, and reuse only complete exact-head gate evidence through the governed lower-level reviewer lifecycle.
- `references/exact-head-probes-and-final-cycle-budget.md` — probe source binding across worktrees/heads, expected-exception red/green evidence, resource-ownership follow-up, full-chain budget reservation, reviewer retry, corrective-cycle classification, and ordered ready-without-merge/tracker closeout barriers.
- `references/reviewer-launcher-write-modes.md` — Codex A/B versus Hermes Auditor write-mode selection, `/tmp` artifact creation, read-only recovery, temp/cache failure classification, and worktree-cleanliness checks.
- `references/stored-gh-credentials-and-relay-attribution.md` — isolate stored `gh`/keychain credentials without breaking model OAuth, freeze reviewer evidence, snapshot IDs immediately pre-relay, and bind readback to the relay-returned immutable ID.
- `references/run-scoped-artifact-hygiene.md` — unique prepared-artifact paths, pre-launch absence barriers, current-run provenance checks, stale-body rejection, and post-readback retention.
- `references/self-hosting-candidate-review-runs.md` — dogfood a candidate control-plane PR with the candidate executable, clean-base source clone, fresh external state/worktrees, parser-compatible isolated Hermes Auditor adapter, process-scoped reviewer relay identity, regular-file wrapper smoke, and quiet background-run discipline.
- `references/process-scoped-relay-identity-and-status-truth.md` — resolve and smoke-test the exact reviewer credential without switching global `gh` identity, classify zero-artifact readback mismatches, and report prepared/validated/launched/complete run states truthfully.
- `references/shared-account-relay-and-feedback-stability.md` — detailed sequencing, verified isolated reviewer identity resolution, relay/readback, immutable-ID ownership, artifact recovery, and deterministic race probes.
