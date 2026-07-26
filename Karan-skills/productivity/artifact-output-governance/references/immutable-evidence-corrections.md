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

A correction should narrow overclaims rather than hide them. Example: historical GitHub App check-suite metadata proves past App activity, not current installation. If the current-state endpoint was misinterpreted, preserve the first bundle, publish corrected semantics with authoritative documentation, re-review, and keep only the corrected manifest canonical.
