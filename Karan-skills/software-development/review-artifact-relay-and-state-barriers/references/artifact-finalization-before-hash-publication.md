# Artifact finalization before publishing evidence hashes

Use this when a gate generates browser reports, screenshots, manifests, or other files whose hashes are published to a PR.

## Failure class

A successful manual gate can produce an evidence directory and hash. If the later prover run executes that same gate again against the same output path, the gate may delete or rewrite the directory after the hash was published. Even when the report and screenshot payloads are unchanged, regenerated manifest bytes can differ. The PR comment then binds a pre-run hash to post-run bytes and an auditor correctly reports a proof-integrity failure.

This is a publication race, not a product-code defect.

## Required sequence

1. Give each evidence-producing run a unique run/head output directory, or make the prover gate read-only when it is consuming already-finalized evidence.
2. Do not publish artifact hashes while any process can still rewrite the referenced path.
3. Wait for the terminal gate/prover process to exit, then prove no writer remains for that path.
4. Verify the finalized directory as a closed set:
   - expected files equal actual files;
   - every child SHA-256 and byte size matches the manifest;
   - media dimensions/types match;
   - report head, deployment/base, and outcome fields match the exact run;
   - live PR head still equals the bound head.
5. Hash the finalized manifest and report only after those checks.
6. Publish the hash-bearing comment, then read back that exact comment and compare the complete body or UTF-8 digest.
7. Freeze reviewer packets only after the readback barrier.

## Recovery when a hash was published too early

For a conversation comment, edit the original comment in place rather than posting an unexplained replacement. Preserve the audit trail inside the body:

- replace the stale hash with the finalized hash;
- append a timestamped correction note explaining which later gate rewrote the artifact and why;
- state what was reverified (child hashes/sizes/dimensions, report head/base/outcome);
- state that repository, deployment, production, and account state did not change;
- fetch the exact comment ID and verify author plus byte-for-byte body readback.

Then run a fresh exact-head audit from a newly frozen packet containing the corrected comment. Do not claim the old auditor result became green merely because the comment was edited.

The corrective audit must still cross the normal transport barriers:

1. validate the reviewer final message and prepared artifact with the shipped parser;
2. create and relay only the sanitized publication copy;
3. capture the POST-returned immutable comment ID and compare the complete GitHub body with the publication bytes;
4. re-run the shipped published-artifact predicate against that exact readback; and
5. perform two stable reads of conversation comments, formal reviews, inline comments, review threads, checks, and live head before advising merge readiness.

A targeted fresh Auditor rerun is appropriate when only the published evidence metadata changed and the product head, governing contract, and already-reviewed upstream artifacts did not. It closes the proof-integrity question without pretending that editing the orchestrator comment retroactively changed the old verdict. If product bytes, gate commands, governing issues, or upstream reviewer evidence changed, use the normal fresh ordered review lifecycle instead.

## Design preference

Prefer immutable run-scoped directories over a shared head-only directory. A head can have multiple evidence-generation attempts; naming only by head makes a later valid rerun silently overwrite the bytes an earlier publication cited.