# Completion reconciliation across long agent sessions

## Trigger
A process status, missing artifact, fresh log, or delayed completion notification disagrees with the recorded lane state. This is an evidence-reconciliation pattern, not a claim that any particular process tool is unreliable.

## Observed successful recovery
During the Hourbook review, an Integration Auditor wait command timed out. A subsequent read found the final review artifact, and the recorded PID was no longer listed; the completed review was incorporated into the repository-readiness handoff. Separately, delayed A/B notifications reported `exit_code=None, reason=exited` after their results had already been incorporated. Those notifications did not change the review conclusion. The lesson is to reconcile existing artifacts and process state before restarting or announcing failure—not to treat a timeout or null exit code as a verdict. The checklist below generalizes that lesson; it is not a claim that every listed check was exercised in that session.

## Procedure
1. Keep a small ledger per lane: role, exact head, command/workdir, PID/process handle, start identity when available, expected final-artifact path, validation state and remote artifact ID if published.
2. Treat a null exit code or missing result as unknown, not pass/fail. Inspect native PID command/workdir/start identity and a bounded progress signal once. Do not print full process environments or secret-bearing arguments.
3. If still active, retain the original run. Prefer its existing completion notification; when reconciling a lost/restored handle, one deadline-bounded watcher may observe completion. A watcher observes—it does not restart, kill or accept the worker.
4. After exit, read the dedicated final-message artifact, not a verdict extracted from mixed transcripts. Validate role, exact head, status/count shape and repository integrity. Attribute saved parent test evidence separately from reviewer-executed probes.
5. Publish only through the existing authorized transport boundary, then read back the immutable ID, author, exact body and applicable commit binding. Record the ID so recovery cannot publish twice.
6. Before relaunching an apparently failed lane, rule out a still-running original and an already-finalized/published result. If identity or completion cannot be established, report unknown rather than inventing an exit status.
7. Deduplicate notifications against the ledger. Already-integrated completion is silent; changed evidence warrants one consolidated update. A completion notice is not a new user request or fresh authority.

## Boundaries
- A live PID does not prove useful progress, and process disappearance does not prove success.
- Do not build a permanent polling service or alter global tools/configuration for a single review.
- Do not claim complete descendant cleanup from a process-group or PID check.
- This recovery does not change review tiers, repair budgets, credentials or merge/deploy authority.
