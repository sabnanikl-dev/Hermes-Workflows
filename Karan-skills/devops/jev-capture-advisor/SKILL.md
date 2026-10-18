---
name: jev-capture-advisor
description: "Use before routing knowledge capture. Ask Jev first."
---

# Jev-first Capture Advisor

Karan requested **Jev's destination suggestion before Hermes reasons through placement**, not a second opinion after choosing a destination. Use at capture/closeout time for a proposed knowledge artifact, not on every message. Default profile only. Skill-guided, not an automatic runtime hook.

## Order of operations

1. **Privacy before inference.** Prepare a short factual description of the proposed artifact and its known purpose. Remove names, paths, client facts, quotations from private notes, URLs and secrets. Do not preselect a destination, add the expected label, or rewrite the description into taxonomy language to steer Jev. Sanitization is necessary; destination reasoning waits until after its response. If a useful summary cannot be made safely, do not send it; handle locally or ask the owner.
2. Honor explicit do-not-save instructions and known sensitive content without a network call. Optional local metadata about mixed ownership or an existing canonical home must reflect facts already established, not a routing judgment made to avoid consulting Jev. No keyword routing baseline runs in production.
3. Send one JSON object on stdin to:

```text
/Users/creator/.hermes/hermes-agent/venv/bin/python /Users/creator/projects/hermes-jev-skills/capture_advisor.py --allow-network
```

Required shape (example is fabricated):

```json
{"summary":"The user wants to preserve why they changed career direction.","privacy_reviewed":true,"do_not_save":false,"contains_sensitive_data":false}
```

Use `subprocess.run` with `input=json.dumps(payload)`, `text=True`, `capture_output=True`, and `timeout=15`; print only stdout, not arbitrary exception/stderr text. Do not pass raw content as command-line arguments or persist an input file. Optional fields: `mixed_ownership` (boolean), `existing_home` (`none`, `personal_vault`, `agent_wiki`, `project_files`, `skill`, `tracker`). Summary limit: 2,000 characters. The CLI rejects unrecognized fields. Without `--allow-network` it reads neither stdin nor credentials.

4. **Now reason and verify.** Interpret `destination`: `personal_vault` = Karan OS; `agent_wiki` = Hermes Brain; `project_files` = project/repository; `no_capture` requires reading `disposition`. Treat confidence as diagnostic, never authority. Inspect primary consumer, evidence and existing canonical location after receiving advice. If overriding Jev, briefly explain the concrete reason; do not conceal the disagreement or repeatedly query until it agrees.
5. For `no_capture`: `discard` means no new capture, not permission to delete; `clarify` means ask rather than silently drop; `split` means separate the artifacts and reassess; `use_existing`, `use_skill`, and `use_tracker` point to their existing owners, not new vault duplicates. `privacy_block` means do not resend more private context. `needs_review`, any fallback, or a timeout returns control to normal Hermes reasoning; no retry/model switching.
6. Any actual read/write uses ordinary approved tools and existing ownership/permission rules. **The advisor cannot write or authorize anything.** Karan OS still requires explicit owner capture/maintenance authorization; a recommendation does not establish a new folder, change a boundary, or permit cross-vault copying. Read back vault edits.

## Capture-hook test discipline

A staged suggestion-only prototype lives in the project’s `capture_hook/`; its `SPEC.md` and `RESULTS.md` distinguish native hook tests from live Jev routing and actual conversational delivery. Do not interpret staged code or green routing tests as live enablement or automatic-save approval.

When testing capture lifecycle adapters, reject missing turn identity rather than reusing old session state, and preserve intentional silence using the host’s canonical predicate. Exercise both through real native dispatch/finalization. Treat omitted candidates as not assessed, not as a no-capture decision; intentionally silent turns must remain silent. Keep candidate privacy review and recommendation/owner-decision/implementation authority separate. Test a deliberately restored defect to prove regressions detect it. Automatic saving still requires an explicit bounded policy and verified exact destinations.

Full-conversation pilots must test ordinary acknowledgements and explicit opt-outs, not only durable findings. Verify that the main model handles Jev's `clarify`/other dispositions transparently in its final answer; an advisor returning correctly does not prove the conversation obeys it. Distinguish an intentional local skip from an omitted assessment without turning every reply into capture bookkeeping. Component tests, a live advisor call, a full model conversation, and platform delivery are separate proof stages.

For live conversational pilots, resolve and verify Hermes' active managed interpreter before launching model code; a legacy checkout venv can pass offline tests yet fail after CLI bootstrap with incompatible compiled packages. Preserve failed-run evidence and verify rollback before a bounded retry. Keep test-only filesystem-audit portability failures separate from plugin failures and from real conversation success; never label a skipped or blocked native suite green.

Treat Telegram usability as a separate acceptance gate from transport. Keep the capture addition to one short natural-language suggestion or question with a clear next action; avoid internal status enums, duplicated clarification, and repeated authority disclaimers. Preserve fail-closed controls in code rather than exposing internal machinery as chat prose. A delivered message can pass transport and still fail owner-facing clarity; record both and keep activation off when the owner rejects the UX.

For managed-Python isolation audits, resolve exact stdlib/dependency roots with `sysconfig`, allow only library reads and the exact optional stdlib ZIP, and enforce write denial independently. Resolve symlinks and test adjacent private paths, library-write bypasses, and network denial with deliberate mutations. Isolate child HOME when scratch sits beneath the live Hermes root, without dropping the original private-root audit. For normal-persona evidence, verify the stored prompt through its hash-linked system-prompts record when the session's inline prompt is null; emit only presence checks, not private prompt contents.

Scope presentation claims to what the component actually observes: a writer-free advisor may say that its check saved no note, not that nothing anywhere was saved. A crash-safe attempt recorded before inference is not a completed assessment; describe deduplicated unresolved attempts as recorded/not retried, never already checked. Preserve this distinction when simplifying copy.

## Boundaries and maintenance

- One request maximum, exact `typesafe/jev-1.13` via the fixed OpenRouter Decisions endpoint. No vault/repository scanning, skill-catalog upload, automatic file creation, hooks or model configuration changes.
- Uses the existing credential privately in-process. The reviewed summary still goes to OpenRouter/TypeSafe; no zero-retention guarantee. The obvious-pattern privacy guard is not comprehensive DLP. Do not send private Karan OS contents.
- Normal CLI runs do not persist summaries/results or echo input. Caller tool/session infrastructure can still retain tool input/output; do not mistake no application log for zero retention.
- Project: `/Users/creator/projects/hermes-jev-skills/`. Read `CAPTURE_ADVISOR.md` for validation evidence and failure semantics. Canonical skill source is `capture_skill/SKILL.md`; synchronize this default-profile copy after edits. Existing `jev-skill-advisor` remains separate and opt-in.
- Disable by not invoking this advisor and removing its reference from the capture workflow; no daemon or gateway restart is involved. Do not delete project/evidence without approval.
- Test with `python -m unittest discover -s tests -v`. `capture_verify.py --allow-network` runs paid synthetic regression, never private inputs; do not automatically rerun it. Previously exposed fixtures are not a new holdout.
