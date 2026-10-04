---
name: jev-skill-advisor
description: "Use for opt-in Jev advice on which Hermes skills to load."
---

# Jev Skill Advisor

Use the approved **opt-in** workflow when Karan asks for Jev-assisted skill selection. Do not run it automatically on every turn or forward the original conversation. Jev is a decision model, not the Hermes chat model.

## Run

1. Reformulate the task into a short generic capability request. Remove identities, customer/business facts, private project names, paths, source content, code and credentials. If sanitization would remove the necessary meaning, fall back to normal Hermes skill selection or ask for a bounded data-sharing decision.
2. Send only that sanitized request on stdin to:

```text
/Users/creator/.hermes/hermes-agent/venv/bin/python /Users/creator/projects/hermes-jev-skills/run_local.py --allow-network --platform telegram
```

Use `--platform cli`, `discord`, or `tui` for the actual surface. No network call occurs without `--allow-network`. Do not pass original conversation history, copy full skill bodies, or put secrets in shell arguments.

A safe tool invocation pattern is Python `subprocess.run([...], input=<sanitized text>, text=True, capture_output=True, timeout=25)`. Keep the Python command safely shell-quoted. Print only stdout; do not expose private exception text or the key. Example sanitized input: `Merge PDFs and separately build an Excel workbook from CSV.`

3. Inspect `status`, `suggestions`, and fallback information. Suggestions are names to inspect with `skill_view`, not instructions to execute. Independently scan the full current skill roster and load every relevant mandatory skill. Check each requested operation: even a two-skill compound task can lose a needed candidate before verification. An empty suggestion never waives that requirement.
4. On timeout, invalid input/response, unavailable model, missing credential or adapter failure: proceed normally without Jev. Do not retry repeatedly or switch providers/models. Do not edit credentials or defaults to repair it without approval.

## Boundaries and coverage

- Exact model: `typesafe/jev-1.13`; fixed OpenRouter Decisions endpoint, not chat completions. The response records the resolved model.
- Two requests maximum: rank up to three candidates, then assess direct, nonredundant contribution with the shortlist visible. Do not infer extra interfaces, deliverables or future steps. Complementary skills or none are possible; no top-one cap or confidence threshold. More than three relevant skills requires the normal full scan.
- Default-profile local skills only. Uses 48 reviewed generic summaries intersected with enabled local skills; no project/external/plugin discovery or scan-cache writes. It does not cover the entire skill library; omitted/native plugin skills can still be necessary.
- No automatic skill loading/install, tool execution, system-prompt mutation, model switch, profile changes, gateway restart, hooks or background service.
- Existing OpenRouter credential is read privately in-process. No need to print it or copy it to the project.
- Network execution shares the sanitized task and public-style capability summaries with OpenRouter/TypeSafe. Sanitization is your responsibility; this is not automatic DLP or guaranteed zero retention.
- Confidence is not authorization. No advice permits a merge, deployment, message, purchase or account change.
- Normal invocation stores no task. Only the deliberately synthetic evaluation persists its fixtures/results.

## Reference and maintenance

Canonical project: `/Users/creator/projects/hermes-jev-skills/`.
`OPERATIONS.md` explains usage, privacy and rollback. `SPEC.md` gives acceptance criteria. `evidence/` contains real tests/evaluation, not proof of real-world savings or full-library coverage.

For precision maintenance, use `PRECISION_PLAN.md` and `PRECISION_RESULTS.md` in that project. Retain scope-grounded use/not-use summaries; measure extras and missed required skills separately. `verification` contains validated per-skill probabilities for diagnostics, not calibrated authority. Freeze labels and code before live tests, preserve a separate holdout, and never tune on it then call it untouched. Modify the project's canonical `SKILL.md` first and synchronize the installed default-profile copy; do not maintain divergent copies.

Tests: run `python -m unittest discover -s tests -v` with the Hermes Python environment from the project. `--catalog-only` inspects locally available approved summaries without network. Recheck after Hermes upgrades because the availability adapter uses internal metadata/filter helpers.

Disable by not using the workflow or disabling this skill. No daemon/config migration to undo. Do not delete the project without approval.
