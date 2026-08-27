# Browser-origin boundary and capability probes

Use this reference when a validator or browser-evidence archive claims that an iframe/provider repair preserves a private or non-bypassable boundary while restoring storage, network, or third-party runtime capability.

## Separate functionality from isolation

A functional repair can invalidate the security contract it must preserve. Green loader, storage, command, request, or evidence-binder checks do not prove non-bypassability when the browser architecture no longer supplies that property.

Test these independently:

1. provider capability: storage, initialization, loader/config/event behavior;
2. parent-to-provider isolation;
3. provider-to-parent isolation;
4. approved message grammar and origin checks;
5. consent/host/no-egress policy.

## Same-origin sandbox warning

A sandboxed iframe with both `allow-scripts` and `allow-same-origin` is not a durable isolation boundary from a same-origin parent:

- child cookies/storage may work;
- child code can access parent DOM, cookies, and local storage;
- `frameElement` can expose the real iframe;
- child code may remove the iframe's `sandbox` attribute;
- parent code that obtains the frame can access the child realm directly, bypassing an intended `MessagePort` command grammar.

A closed shadow root reduces ordinary enumeration but is not an origin boundary. Assertions such as `window.frames.length === 0`, `host.shadowRoot === null`, no visible iframe, or no top-page queue prove non-enumerability only.

For remotely updated third-party code, probe both directions:

- **Parent → child:** can page code obtain a realm handle and inject arbitrary data or script without using the approved port/grammar?
- **Child → parent:** can provider code read the parent URL, DOM, consent storage, cookies, or execute parent-realm script?

## Separate-origin positive control

Use two real local origins (distinct ports suffice) for the red/green architecture control:

- **red / same origin:** provider storage works, and parent DOM/storage access should also work; the probe must expose why this is not containment.
- **green / separate origin:** provider storage on its own origin works, while parent DOM/storage access raises `SecurityError` and `frameElement` is `null`.

This proves only the browser-origin property. A production design still needs an exact provider-origin allowlist, consent gate, fixed message grammar, request interception before merge, and separately approved live proof.

## Non-vacuous test rule

A containment probe is evidence only if its unsafe state can actually be constructed and the probe fails on it.

Red flags:

- reading `window[0]` while separately asserting `window.length === 0`;
- hand-authoring an impossible JSON mutant rather than producing the unsafe browser state;
- treating no visible iframe or closed-shadow enumeration as isolation;
- proving only that the approved message channel is bounded while ignoring direct realm access.

For every claimed boundary, create a real-browser red/green pair and record raw observed outputs—not inferred labels. Before promoting a new assertion into an evidence binder, force the prohibited state and watch the public producer/checker reject it.

## Review and workflow response

When adversarial review shows an implementation cannot satisfy a load-bearing boundary requirement:

1. distinguish `artifact/functionality correct` from `guard/security claim unsound`;
2. independently reproduce the architecture property against the exact remote head;
3. keep or convert the PR to draft rather than presenting it as merge-ready;
4. stop broad reviewer fan-out when the confirmed architecture blocker already prevents approval;
5. reconcile GitHub and the owning tracker with the exact head and reproduced result;
6. escalate the smallest explicit decision: accept/rewrite the security trade, authorize the broader architecture needed to preserve it, or retire the draft and leave the feature inert.

Passing repository tests, preview checks, and intercepted browser QA are insufficient when the required property is demonstrably false. Do not silently broaden into DNS, hosting, account, deployment, or provider-origin mutations when the governing issue lists them as out of scope.