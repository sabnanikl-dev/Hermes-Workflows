# Correcting immutable evidence without erasing history

Use this pattern when a content-addressed evidence bundle contains a semantic overstatement but its hashes and raw observations remain internally valid.

1. Do not edit the existing hash-addressed directory in place.
2. Correct the source/generator and build a new content-addressed bundle.
3. Preserve the old bundle as historical evidence, but mark its manifest and review as superseded in the authoritative tracker.
4. Explain exactly what changed and what did not. Distinguish a corrected interpretation from a changed terminal decision.
5. Rerun independent review against the corrected manifest; never reuse a review bound to the superseded bytes.
6. Store and read back the corrected review by its own digest.
7. Update parent and child trackers with the canonical manifest/review hashes and state explicitly that prior hashes are not valid for decision-making.
8. Verify the final tracker comments directly by comment ID when connection ordering (`first`/`last`) is ambiguous.

## Presentation-only repair while review is active

A formatting fix changes the reviewed bytes even when no fact changes. Preserve the in-flight candidate; create a separate revision rather than patching the files beneath the reviewer.

1. Correct both the generated artifact and its generator. Update staging locators only where needed; preserve provider captures, timestamps, normalized data, and provenance unchanged.
2. Exercise the actual rendering defect before freezing the new revision. For generated Markdown tables, a table-enabled parser should produce the expected number of body rows, not merely find pipe characters in the source.
3. Produce a new manifest with an explicit predecessor/supersession binding. Programmatically enumerate changed paths and verify unchanged evidence hashes.
4. Give the reviewer the new exact report/manifest hashes and the bounded delta. The reviewer may carry substantive checks forward **only after independently verifying unchanged evidence and the exact presentation-only diff**, then issue a new verdict explicitly bound to the new revision. This is fresh delta acceptance, not reuse of an old-hash verdict. If data, meaning, claims, or authority changes, review the affected substantive scope instead.
5. Read back that verdict and verify its hash before canonical promotion. Update tracker payloads and delivery archives to the accepted revision; verify archive entries against canonical file hashes. An asynchronous reviewer result is not the handoff until promotion and exact-target tracker readbacks are complete.

### Exercised Markdown smoke-check pattern

With `markdown-it-py` available, the following logic detects detached table bodies. Choose expected counts from the actual report contract/dataset; do not fossilize one report's counts:

```python
from markdown_it import MarkdownIt

tokens = MarkdownIt().enable('table').parse(markdown_text)
body_counts = []
inside_body = False
rows = 0
for token in tokens:
    if token.type == 'table_open':
        rows = 0
    elif token.type == 'tbody_open':
        inside_body = True
    elif token.type == 'tr_open' and inside_body:
        rows += 1
    elif token.type == 'tbody_close':
        inside_body = False
    elif token.type == 'table_close':
        body_counts.append(rows)
assert body_counts == expected_body_counts
```

A paired analytics report exposed this failure as `[5, 5, 0]` instead of `[5, 5, 5]`; removing one blank line and correcting the generator restored the body without changing evidence. The independently accepted replacement used a new manifest and verified exact delta. Parser success is structural presentation evidence, not a substitute for numeric or factual review.

A correction should narrow overclaims rather than hide them. Example: historical GitHub App check-suite metadata proves past App activity, not current installation. If the current-state endpoint was misinterpreted, preserve the first bundle, publish corrected semantics with authoritative documentation, re-review, and keep only the corrected manifest canonical.
