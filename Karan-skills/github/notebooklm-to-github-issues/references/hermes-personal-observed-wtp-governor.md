# Hermes Personal Observed-WTP Governor Pattern

Use this pattern when Product 001 or a similar passive-revenue scout has enough buyer-language/proxy evidence to look organized, but public launch is still blocked by observed willingness-to-pay proof.

## Trigger

Apply when the active product has:

- repo-local clarity/packaging validators passing;
- several promoted proxy experiments (copy clarity, objection coverage, proof maps, artifact rebuilds);
- an adversarial or human blocker that says willingness-to-pay is still unproven;
- a prose gate that future agents might accidentally treat as resolved because adjacent buyer voice or category evidence exists.

## Pattern

Create a small deterministic governor instead of more copy/artifact polish.

1. Keep the normal research/artifact command in report mode so cron runs can continue safely.
2. Add a strict `--require-pass` mode for approval/public-live checks.
3. Count only explicit machine-readable markers, e.g. `WTP-VERIFIED: ...`, that include:
   - verifiable URL;
   - target or clearly comparable buyer class;
   - paid/purchase/would-pay/review/sales signal;
   - mapping to one kit artifact/job;
   - caveat/source-bias note.
4. Ignore the documentation/template marker itself so the example cannot accidentally count as evidence.
5. Keep the current state honest: if the gate is `0/3`, report it as blocked even when other validators are green.
6. Wire the strict command into the product governor/readiness docs before any public-live approval request can be drafted.
7. Append exactly one experiment-ledger row for the evidence/WTP gate surface.

## Verification pattern

When a verifier asks for fresh evidence on the new governor script, use a temp script under the requested temp directory with prefix `hermes-verify-`.

Strong assertions:

- expected red: no markers -> blocked;
- expected red: template/example marker -> ignored;
- expected red: malformed marker -> scanned but rejected;
- expected green: three complete markers -> pass in isolated fixture;
- live repo: report mode succeeds while `--require-pass` exits non-zero if the live gate remains unresolved;
- cleanup: temp script deleted and `TEMP_SCRIPT_EXISTS_AFTER_CLEANUP=False` printed.

If the module computes repo-relative paths with `ROOT`, and the fixture lives outside the repo, monkeypatch `ROOT` together with the target path constants during the isolated fixture. Restore all monkeypatched constants in `finally`.

## Pitfall

Do not record the governor as market progress. The product decision remains `blocked` or `hold` until evidence clears the strict gate or Karan explicitly overrides the gate. The governor is a harness improvement that prevents false-green launch readiness.