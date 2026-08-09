# Fail-Closed Client Revocation Probes

Use for client-side consent/collection wrappers where revocation must outrank storage and analytics-provider state.

## Safety invariant

After a decline attempt returns—whether or not persistence or provider notification succeeds—the current document must be locally unable to collect. A previously readable `granted` value must not reactivate it.

## Required ordering

1. Capture whether a tag/runtime was active only for best-effort notification.
2. Record an in-memory revocation.
3. Disable all local enabled/initialized state.
4. Preserve the fact that an existing loader is already loaded; do not unload it or insert another on a later grant.
5. Best-effort a provider `consent: denied` notification only for a previously active tag. Do not create a queue/loader for an inactive decline. Catch only this provider handoff.
6. Attempt persistence and make the public return value truthful about persistence, not about whether local revocation happened.

A later grant can clear the in-memory revocation only after that grant itself was successfully persisted and eligibility gates still pass.

## Former-red probe matrix

Start each case with an eligible active page, one inserted tag, a prior readable `granted` record, and at least one initial event.

| Fault | Required post-decline proof |
|---|---|
| `localStorage.setItem` throws | No outward throw; local state disabled; denied provider update attempted when queue works; readable old grant cannot reactivate `send`, `init`, or click; persistence return is false; no second loader. |
| Provider `dataLayer.push` throws | No outward throw; local state disabled **before** the attempt; denied update attempted exactly once; later actions do not retry/emit; stored decline return remains truthful; no second loader. |
| Both throw | Same local safety proof; persistence return false; provider failure cannot affect revocation. |
| Inactive/no-consent decline | No `dataLayer`, no loader, no provider queue created; state stays disabled. |
| Ordinary active decline | Existing provider queue receives the arguments-like denied update; loader remains one; re-grant does not duplicate the tag. |

## Mutation sensitivity

Use the same probes against deliberate source mutations. They must fail when any of these occur:

- storage persistence returns before local revocation;
- provider queue handoff precedes local revocation;
- provider queue exception is uncaught;
- in-memory revocation is removed;
- enabled state is not cleared;
- provider notification is skipped for the ordinary active case.

## Exact-head discipline

If the repair is pushed, do not launch the final PR review merely because `git ls-remote` sees it. Wait until the PR's `headRefOid` matches local HEAD too. If a final review discovers another blocker after an explicit “stop after review” instruction, report it without silently adding another repair cycle.
