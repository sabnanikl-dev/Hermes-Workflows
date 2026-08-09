# Browser provider authority: realm split and finite proof

Use this reference when a third-party browser provider requires a mutable realm-global queue, while the product contract forbids exposing mutable event or payload authority to ordinary page code.

## Architectural decision

A same-realm getter, symbol, proxy, frozen wrapper, or `document.currentScript` condition is not private authority. Code in that realm may recover or spoof the condition and reach the queue. Repeatedly patching accessors is a stop signal.

The smallest defensible boundary is usually a separate browser realm:

- hidden iframe inside a **closed** shadow root;
- `sandbox="allow-scripts"` without `allow-same-origin`;
- provider queue, provider function, and direct loader only inside the opaque child realm;
- parent iframe/channel references held in a closure;
- all production, host, consent, and configuration gates run before frame/channel/listener/observer creation;
- no top-page tracking/configuration API beyond any explicitly approved zero-argument wake-up.

The child may keep its required mutable queue because ordinary top-level code cannot access the child global. Count all served executable provider logic against any size/proportionality ceiling; moving code into a child file must not game the metric.

## Threat-boundary discipline

State what “private” means. The realm split can protect against ordinary top-level code after reviewed initialization: global mutation, queue probing, `document.currentScript` spoofing, arbitrary later window messages, repeated boot, and later prototype changes when required intrinsics were captured.

It does not claim to defeat hostile code that ran first and replaced `attachShadow`, `MessageChannel`, `crypto`, or event registration; XSS that can send its own requests; extensions/DevTools; or a compromised provider script. Unless the governing issue names those threats, treating them as blockers recreates a general sandbox framework around a small product seam.

Optional stronger handoff hardening—random fragment token, exact source/origin, one accepted port, bound `postMessage`, numeric opcodes—should be added only when the frozen threat model requires it. Do not convert every reviewer idea into mandatory infrastructure.

## Non-circular browser qualification

Do not expose a top-page debug queue to observe the child; that recreates the authority surface under test.

A proportionate real-browser producer should:

1. intercept every request;
2. abort all real analytics/ads traffic;
3. fulfill the intercepted provider-loader request with a tiny laboratory stub running inside the opaque iframe;
4. have that stub observe child queue pushes and attempt synthetic collection requests containing normalized provider commands;
5. intercept and abort those collection attempts in the Playwright process;
6. assert payload grammar, fixed URL/referrer, event names/enums, bounded integers, and zero real egress at that network boundary;
7. track loader attempts separately from collection attempts.

This proves provider-bound behavior without publishing the queue, iframe, shadow root, or port to page code.

## Former-red probes

At minimum, prove:

- committed-disabled bytes create no frame, channel, listener, observer, loader, or request;
- eligible bytes create one opaque frame and one loader attempt;
- no top-page `dataLayer`, provider function, queue, port, or broad API exists;
- no light-DOM iframe or open shadow root is reachable;
- shadowing `document.currentScript` and creating PII-bearing fake globals does not alter provider calls;
- arbitrary later window messages do not create commands;
- repeated wake-up creates no second frame, loader, config, or page view;
- hostile URL/query/referrer/DOM values never cross the provider boundary;
- desktop/mobile intercepted runs report zero real egress.

A deterministic checker may use a fixture-only privileged child handle, but production bytes must not expose that handle. Mutation checks should reject public queue/port exposure, open/same-origin sandboxing, URL-override removal, permissive consent, global authority rereads, and duplicate startup.

## Proof-layer boundary

Keep three claims separate:

- runtime checker executes shipped behavior against fresh literals;
- browser producer performs the trusted exact-head execution and its process exit is authoritative;
- narrow binder checks successful outcome, empty problems, runtime path/hash/commit, required scenarios/viewports, screenshots, and high-level no-egress/event observations.

Archived JSON/screenshots are repository evidence, not hostile production input. Unknown fields are non-blocking unless they hide failure, alter binding, or contradict required observations. A generalized hostile-report validator is architecture drift, not stronger product proof.

## Stop rule

If a bounded replacement uses its one approved review-driven fix and the ordered unchanged-head reviewers still reproduce a real authority bypass, stop that PR. Preserve it as read-only evidence, freeze the continuation decision in the issue, and start a fresh replacement from the current approved base rather than granting silent extra repair cycles or expanding the checker.
