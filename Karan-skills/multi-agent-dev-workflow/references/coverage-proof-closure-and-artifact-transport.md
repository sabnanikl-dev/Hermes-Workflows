# Coverage-contract proof closure and reviewer-artifact transport

Use this when an ontology/schema PR claims durable client coverage through competency questions, or when reviewer output is relayed from credential-free child processes.

## Coverage status must close over evidence and executable retrieval

A matrix cell labeled `covered` is only credible when all three links close:

1. **Canonical evidence:** every resource used to support the claim has legitimate evidence under the repository policy. A passing test over draft or zero-evidence objects proves consistency, not source-backed coverage.
2. **Exact competency retrieval:** the cited competency actually selects the identity, offering, audience, system, role, metric, or flow named in the matrix cell. A governance-rule question does not prove brand identity or offerings merely because it concerns the same client.
3. **Runtime/test boundary honesty:** documentation states whether the answer is available through a public consumer operation or only through a test-owned runner.

Review each `(family, client)` cell as a producer/consumer closure:

| Cell claim | Canonical objects | Evidence refs | Competency ID | Selected output | Public consumer or test-only |
|---|---|---|---|---|---|

Block when any claimed object is absent from the competency output, lacks required evidence, or is available only in a narrower maturity dimension than the cell claims. Fix by one of three honest paths:

- add legitimate evidence and exact competency proof;
- split a broad family into independently statused subrows;
- downgrade to `known gap` or `deferred/trigger-gated` and mark any retained question optional/planning-only.

Never fabricate evidence or promote draft/proposed resources to make the matrix green. Making a relationship question optional does not resolve an unevidenced required entity question that still backs a `covered` cell.

## Current-head count derivation

When a JSON test report stores groups as objects such as `{passed, cases}`, count `len(group["cases"])`, not `len(group)`. Before launching reviewers, assert machine-derived totals against PR metadata and print the meaningful split (for example rejection cases vs valid controls). Reject a packet whose totals disagree with executable output.

## Exact reviewer-artifact extraction

Reviewer prompts themselves often mention `BEGIN_ARTIFACT` and `END_ARTIFACT`. Substring extraction can therefore capture prompt text rather than the prepared review.

Parse delimiter **lines exactly**:

```python
lines = Path(output_path).read_text().splitlines()
start = next(i for i, line in enumerate(lines) if line == "BEGIN_ARTIFACT")
end = next(i for i, line in enumerate(lines[start + 1:], start + 1) if line == "END_ARTIFACT")
body = "\n".join(lines[start + 1:end]).strip() + "\n"
```

Before relay, assert the expected role signature, full head SHA, runtime line, and transport disclosure. Then re-query the live PR head, relay under the verified reviewer identity, and read the posted artifact back. If extraction validation fails, post nothing; correct the parser and retry.
