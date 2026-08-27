# Local Service Availability Crons

Use this pattern when a recurring local automation depends on a long-running server such as n8n, but the user wants the cron to do nothing beyond keeping that server available.

## Contract

The cron is an **availability ensure**, not an execution trigger:

1. Check the service health endpoint and expected listener port.
2. Read-only verify the exact approved workflow/job is present and active when a local state store makes that possible.
3. If healthy, make no changes.
4. If the expected port is occupied but health fails, fail closed; do not kill or replace the unknown listener.
5. If down, the port is free, prerequisites exist, and the approved workflow is active, start the server as a Hermes-tracked background process. If configuration lives in a dotenv-style file whose assignments are not prefixed with `export`, use `set -a; source <env-file>; set +a` (or an equivalent verified env loader) so the child process actually inherits the variables. A plain `source <env-file>` only creates shell variables and can silently launch the service with fallback/test configuration.
6. Recheck HTTP health and the listener before reporting success. Also verify one non-secret configuration sentinel from the child process or the next read-only execution record (for example, production-vs-test mode/project identity); process health alone cannot prove the intended runtime configuration was inherited.
7. Never manually execute, import, publish, activate, deactivate, or edit the dependent workflow unless separately authorized.

## Hermes Cron Shape

Prefer an **agent cron with only the terminal toolset** when keeping a process alive requires `terminal(background=true)`. Put the exact working directory, environment-loading step, version pin, health URL, port, and forbidden mutations in the self-contained prompt.

Do not use a script-only cron to daemonize a server with shell `&`, `nohup`, `launchctl submit`, `systemctl`, or a custom respawn loop. Hermes lifecycle guards intentionally reject persistent supervisor patterns that could create SIGTERM/respawn loops. Use Hermes background-process tracking instead.

Use local delivery when routine healthy results should not interrupt the user. If the user wants operational alerts, use a separate quiet script-only health watchdog that emits only on failure; keep that watchdog read-only and do not make it a second process supervisor.

## Scheduling

When the service hosts its own internal schedule, run the availability ensure shortly **before** a known internal trigger rather than at the same minute. Example: ensure at 05:50 for an internal 06:00 reconciliation. This gives startup and health verification time without manually triggering the workflow.

A once-daily ensure only helps while the machine and Hermes scheduler are awake. State that boundary explicitly; do not imply cloud-grade uptime for a local Mac-hosted process.

## Verification

After creating the cron:

- Run it manually once while the service is already healthy; this proves the no-op path and avoids mutating downstream data.
- Recheck the health endpoint, listener, and approved workflow active state.
- Inspect the latest scheduled/trigger-mode execution, not only the server process. A healthy listener plus `active=true` can coexist with repeated downstream authentication or configuration failures.
- Compare the latest trigger time with the current server process start. If no trigger has run since startup, require verified non-secret runtime sentinels; if one has run, require the expected production mode and successful status before calling the automation healthy.
- Keep availability and execution ownership separate: the ensure cron may start/verify the service, but the hosted automation must perform reconciliation and downstream writes. Do not compensate for a broken workflow by manually reproducing its Drive/CMS/site work.
- Re-list the cron and verify enabled state, exact recurring schedule, delivery mode, last status, and non-null next run.
- Confirm the test did not change workflow configuration or manually execute downstream automation.
