# Privacy-Sensitive Analytics Architecture Review

Use this reference when reviewing an analytics/consent architecture whose governing requirement is **zero vendor execution and zero vendor network traffic before explicit opt-in**.

## Separate the control planes

Do not collapse these into one “event allowlist” claim:

1. **Consent startup** — local queue creation, consent-default commands, vendor library load, and network egress are distinct events.
2. **Application events** — fixed wrappers can constrain only events emitted by application code.
3. **Vendor automatic events** — lifecycle events may still be generated after the vendor runtime loads.
4. **Enhanced measurement/property settings** — property-level features must be explicitly accepted, disabled, and evidenced.
5. **Page and attribution fields** — URL, referrer, route, campaign, and query handling need their own contract.
6. **Revocation** — stopping application dispatch, issuing a denied update, persisting denial, bounded cookie cleanup, and unloading via navigation/reload are separate steps.

## Consent semantics

- Distinguish **Basic tag blocking** from denied-state loading. If the requirement is zero vendor traffic before opt-in, the vendor library must not load before consent.
- A local queue is not itself network traffic. Describe queue timing accurately and label any sequence not directly documented by the vendor as inference or a project-specific equivalent.
- Do not claim that a denied storage setting guarantees zero traffic after a vendor tag has loaded.
- Persisted-grant pages must reconstruct the required consent-command order before the library processes commands.

## Revocation review

Reject persistence-plus-reload as the entire flow. Require:

1. synchronously stop application dispatch;
2. send the documented consent downgrade when a loaded runtime exists;
3. persist the non-granted state;
4. perform only bounded best-effort cleanup of known script-removable cookies, with explicit scope and non-guarantee;
5. immediately navigate/reload to discard the loaded runtime;
6. prove the fresh document returns to zero vendor state and traffic.

Call out the race window if dispatch is not stopped before the consent downgrade and navigation.

## Exact inventory gate

Freeze an explicit table before implementation:

- manual page views and duplicate-suppression behavior;
- automatic lifecycle events accepted after consent;
- Enhanced Measurement features enabled and disabled;
- every exact application event name and bounded parameter grammar;
- approved-but-unwired events;
- campaign registry behavior;
- `page_location` and `page_referrer` composition.

A category label such as “CTA/showroom/blog wrappers” is insufficient. Enumerate the runtime names.

## URL, referrer, and attribution safety

- Preserve the repository’s existing route/attribution contract; do not replace it with vague “sanitized URL/path” language.
- Use a full canonical URL when the vendor requires one, composed from an approved origin and manifest/build-owned route.
- Never default to raw `location.href` or raw `document.referrer` when the policy forbids arbitrary query/referrer data.
- Accept campaign values only through an exact, complete, active, owner-reviewed registry tuple.
- Reject partial, unknown, retired, duplicate, mixed, encoded, and PII-like query input.

## Browser security claims

- A closed shadow root is implementation hiding, not an origin security boundary.
- A same-origin sandboxed iframe with scripts and same-origin capability cannot honestly be called non-bypassable by same-origin code.
- A separate origin can restore same-origin-policy isolation, but that does not prove ordinary top-level analytics storage, attribution, page context, partitioning, or vendor-supported semantics.
- Keep browser-enforced isolation claims separate from vendor-supported website tagging architecture.

## Alternatives

- Server-side tagging still needs a browser collection/consent design; it is not a standalone pre-consent fix.
- Measurement Protocol is supplemental and requires explicit identifier/session/event modeling; do not present it as a transparent browser-tag replacement.
- Same-origin endpoint-routing guidance does not imply support for running the browser tag in an iframe.

## Proof matrix

Pre-merge tests should intercept and abort every vendor request and report attempted/aborted/delivered counts, with delivered fixed at zero. Cover:

- no choice, dismiss, decline, malformed storage, revocation revisit;
- local, preview, alternate, and lookalike hosts;
- first grant and persisted grant;
- repeated wake-up/idempotency;
- exact automatic, enhanced, and application event inventory;
- page/referrer/campaign fields and hostile query cases;
- revocation and re-grant;
- all supported browser engines when browser behavior is load-bearing.

Live delivery and vendor-side readback remain a separately approved post-deploy gate.
