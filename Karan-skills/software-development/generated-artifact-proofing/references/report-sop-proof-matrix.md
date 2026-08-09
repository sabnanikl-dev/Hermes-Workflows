# Report / SOP Proof Matrix

Use this compact matrix during implementation and exact-head review.

## Producer/consumer seam

- [ ] Capture one payload in the producer’s real emitted shape.
- [ ] Feed it directly to the generator/normalizer.
- [ ] Assert workflow/run identity survives.
- [ ] Assert every required count and reason survives.
- [ ] Assert runtime/file failures survive.
- [ ] Assert guard/abort and trigger/environment metadata survive.
- [ ] Keep the producer-shaped payload as a regression fixture.

## Owner-safe boundary

Inject each value into labels, names, failure summaries, and recommended actions where accepted:

```text
Bearer abcdefghijklmnopqrstuvwxyz123456
token=private-value
customer@example.com
private-folder-id
private-file-id
private-execution-id
```

- [ ] Owner-safe output contains none of the injected sensitive values.
- [ ] Raw execution ID is not used as a fallback owner label.
- [ ] Operator mode retains only intentionally allowed diagnostics.
- [ ] The test exercises centralized projection/redaction, not only known fixtures.

## Unknown/inconsistent state

- [ ] `{}` does not render success.
- [ ] Missing Drive/list state does not render succeeded.
- [ ] Missing guard state does not render “not fired.”
- [ ] Missing archive reasons do not become zeros.
- [ ] Failed count without failure detail is rejected or clearly unknown.
- [ ] Contradictory totals are rejected.
- [ ] `generatedAt < runTimestamp` is rejected.

## Fixture provenance

- [ ] Every fixture is explicitly source-backed or synthetic.
- [ ] A source-backed fixture represents one execution/readback state.
- [ ] Synthetic data carries no real execution identity.
- [ ] Domain count invariants are validated.
- [ ] Regeneration leaves a clean worktree or matches committed hashes.

## Responsive semantics

- [ ] Happy, failure, and guard/archive states captured at the smallest required width.
- [ ] No page/component overflow or clipping.
- [ ] Hidden table headers are replaced by visible/assistive per-cell labels.
- [ ] Long IDs/paths/errors wrap without losing the field label.

## Print completeness

- [ ] PDF is nonblank with plausible page count.
- [ ] Representative pages visually inspected.
- [ ] PDF text extracted.
- [ ] Every required SOP/operator section body appears in extracted text.
- [ ] Closed `<details>`/accordion bodies print, not only summaries.
- [ ] Print proof is recaptured after the final head change.

## Integrated exact-head closeout

- [ ] Branch divergence and semantic conflicts inspected.
- [ ] Current-main validation/build scripts preserved.
- [ ] Feature-specific commands preserved.
- [ ] Complete integrated suite passes.
- [ ] Remote PR head equals verified local head after push.
- [ ] Tests, generated artifacts, screenshots, PDF, and review artifacts all cite the same head.