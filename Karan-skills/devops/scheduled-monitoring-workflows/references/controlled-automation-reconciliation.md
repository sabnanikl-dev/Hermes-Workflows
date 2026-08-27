# Controlled Automation Reconciliation

Use this when an approved scheduled reconciliation must be exercised immediately, but the operator must not manually reproduce the automation's downstream behavior.

## Principle

The hosted automation remains the worker. Hermes may repair runtime availability/configuration and invoke one bounded execution, but must not replace the workflow by directly copying source files, creating target records, or editing the consumer surface.

## Safe sequence

1. Verify explicit approval covers one production reconciliation and its expected downstream writes.
2. Stop the running automation server before CLI execution when the CLI and server would contend for local broker/state ports.
3. Export the exact installed workflow and preserve it as the restore artifact. Confirm identity, active state, schedule, node count, credential references, and reviewed graph invariants.
4. Prepare a temporary runnable copy by adding only one execution trigger wired into the workflow's normal first processing node. Do not duplicate, rewrite, or bypass reconciliation logic.
5. Set only the temporary copy inactive and import it.
6. Load production dotenv configuration with `set -a; source <env-file>; set +a`; set a non-default runner/broker port if required; execute the workflow once through its native runtime/CLI.
7. Use a trap/finally restoration path that reimports the exact saved workflow and republishes/reactivates it even when execution fails.
8. Verify restoration before interpreting success:
   - temporary trigger count is zero;
   - original schedule trigger is present;
   - workflow is active/published as before;
   - node count and reviewed graph invariants match;
   - credential-reference shape and schedule are preserved.
9. Inspect the saved execution and workflow-produced summary. Require success, zero unexpected failures, and safety-guard status.
10. Read back the target system independently using source identifiers. Verify automation-created records/assets/status rather than recreating them manually.
11. Restart the server with exported production variables and verify health, listener, active workflow, and non-secret runtime sentinels.
12. Run the availability cron once to prove its healthy no-op path under the repaired runtime.

## Reporting

State the authority split explicitly:

- Hermes repaired/verified runtime configuration and initiated one bounded execution.
- The automation listed the source, computed reconciliation, imported/touched/archived records, and produced its run summary.
- Independent readback verified the results.
- Hermes did not directly perform the source-to-target content work.

## Pitfalls

- Do not call a server healthy merely because its health endpoint responds and the workflow is active; inspect scheduled execution status and production/test mode.
- Do not use plain `source` for non-exported dotenv assignments when launching a child process.
- Do not import a sanitized repository artifact wholesale over a live workflow; preserve runtime credentials, schedule, IDs, and settings from the live export.
- Do not leave the temporary trigger installed or the scheduled workflow inactive.
- Do not turn an endpoint/TLS verification problem into a claim that reconciliation failed when execution evidence and authenticated target readback prove convergence; report endpoint verification separately.
