# Hermes Personal Path Decision Gate Pattern

Use this when Product 001 or another Hermes Personal passive-revenue product has enough repo-local artifacts/evidence, but the remaining blocker is a human path choice rather than another buyer-facing asset.

## Trigger

- Product artifacts, proof maps, dist files, and validators are green or mostly green.
- A value-clarity or buyer-direction blocker is still active.
- Adversarial review warns that crons are drifting into proxy polish, setup posture, or launch readiness without a human path decision.
- A path decision packet already exists or should exist, but future crons need deterministic enforcement.

## Pattern

1. Query required NotebookLM notebooks and synthesize outside NotebookLM.
2. Prefer a loop/harness move over another product artifact when the product governor says repo-local convergence is achieved.
3. Add or update a `path-decision-packet.md` with a bounded one-reply decision set.
4. Add an adversarial stress-test section that names why each path should be rejected/deferred.
5. Wire a deterministic gate into an existing validator, usually `scripts/strategic_alignment_gate.py`, so active blockers require:
   - all one-reply path options;
   - the adversarial stress-test section;
   - no setup-ready posture;
   - no raw WTP `PASS` labels in launch-facing docs when exact-kit sales remain unproven.
6. Log exactly one product experiment row using `product direction / approval gate` or similar as the single surface.
7. Verify with both normal repo validators and an ad-hoc red/green fixture for the changed gate.

## Verification recipe

A strong ad-hoc verifier should monkeypatch the gate module's `ROOT`, `PRODUCT`, `VALUE_RESET`, `PROOF_MAP`, `LAUNCH_PACKET`, `PATH_PACKET`, and `APPROVAL_FACING_FILES` constants to a temp fixture, then assert:

- red: missing one required path option fails and names the missing option;
- red: all options but no `Adversarial stress-test` section fails;
- green: all options plus the stress-test section passes;
- cleanup: fixture and temp verifier script are removed.

Use an OS-safe tempfile path with `hermes-verify-` prefix when a verifier/system prompt requests fresh evidence.

## Pitfalls

- Do not turn this into another launch packet or buyer-facing deliverable. The point is to stop polish drift.
- Do not bundle public approval, private setup, checkout, waitlist, outreach, or claims into the path packet.
- Do not treat comparable WTP evidence as exact-kit sales proof; keep proof posture separate from approval readiness.
- If the verifier fails due a script quoting/syntax mistake, rerun with a simpler tempfile bootstrap and report the successful fresh run only.