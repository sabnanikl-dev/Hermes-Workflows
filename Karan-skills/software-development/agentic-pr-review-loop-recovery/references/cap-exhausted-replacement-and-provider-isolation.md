# Cap-exhausted replacement restart and top-level provider isolation

Use this reference when a product-first replacement consumes its one repair cycle, the exact-head triad still finds a real blocker, and the owner chooses to continue through another clean replacement rather than weaken the rubric.

## Control-plane sequence

1. Treat the failed replacement as terminal. Do not patch or merge it by exception.
2. Return the decision to the owner with the exact reproduced blocker and truthful consumed-cycle count.
3. If the owner explicitly authorizes continuation, amend the authoritative issue **before another builder starts**. State that the decision authorizes a new replacement attempt, not another repair cycle on the stopped PR.
4. Preserve the original finite proof contract, reviewer rubric, and human merge boundary. Give the new replacement its own bounded cycle only when the issue explicitly says so.
5. Start from current default-branch state in a fresh branch/worktree. Do not cherry-pick stopped-PR commits or inherit their ancestry. Reuse only independently verified product behavior, required wiring, and scenario knowledge.
6. Keep the stopped PR open as read-only evidence until the new replacement PR exists, then close it as superseded.
7. Add the previous blocker as a named former-red test before claiming the new architecture closes the class.

This is a restart of the replacement process, not a hidden extra cycle. The issue amendment is the durable authority record.

## Provider-authority lesson

A conditional top-level getter is not an isolation boundary. In particular, exposing a provider queue only when `document.currentScript === loader` remains bypassable when page code can find the loader and shadow or replace `document.currentScript`. A non-enumerable, non-configurable accessor can still return the live mutable queue under the forged condition.

For direct browser analytics that requires provider-owned mutable state, a stronger class of design is:

- create a hidden host with a **closed** shadow root;
- place the provider iframe inside that root so ordinary top-level selectors cannot recover it;
- sandbox the iframe with `allow-scripts` but without `allow-same-origin`, making its realm opaque to the parent page;
- keep `dataLayer`/`gtag` and the direct provider loader inside that child realm;
- retain iframe, shadow-root, and `MessagePort` references only in parent/child closures;
- bootstrap a private `MessageChannel` without broadcasting a child-ready capability on `window`;
- expose only the issue-approved zero-argument boot seam on the top page;
- keep URL overrides and closed event/payload authority in reviewed code, and test both sides of the channel rather than trusting transport shape.

A closed shadow root is encapsulation, not a cryptographic defense against arbitrary JavaScript that monkeypatches platform prototypes before the runtime starts. Freeze the actual threat boundary in the issue. The required former-red probes should at minimum cover ordinary top-level code after page/runtime initialization:

- enumerate globals and `window.JMD` keys;
- query for provider iframes/loaders and inspect reachable shadow roots;
- shadow/replace `document.currentScript` with any visible script;
- assign likely queue/global names and attempt PII-bearing queue injection;
- attempt arbitrary `window.postMessage` traffic;
- prove the provider call ledger is unchanged except for real fixed interaction-state transitions.

In trusted browser QA, instrument a copied laboratory runtime or return sanitized call snapshots over the private test channel. Never expose the live queue merely to make the harness easier to observe.

## Feasibility spike before product code

Before implementing, run a disposable real-browser spike proving the isolation primitives actually behave as assumed:

- `document.querySelectorAll("iframe")` cannot see the iframe inside the closed shadow root;
- the host's `.shadowRoot` is `null`;
- top-level `window.dataLayer` and `window.gtag` remain undefined;
- no capability-bearing child-ready event is broadcast on `window`;
- the private port still carries one fixed test command;
- the current-script spoof reveals no queue or command authority.

Do not mistake removal of an iframe's `srcdoc` attribute after insertion for secrecy: browsers may cancel the navigation, so prove such lifecycle assumptions in Chromium instead of reasoning from markup alone.

## Concurrency pitfall

Do not run baseline/final verification in a worktree while a delegated builder is actively mutating it. The command can observe a half-written runtime paired with an old checker and produce a misleading failure ledger. Either run baseline before dispatch, give the builder an isolated worktree, or wait for the mutating lane to finish and then verify the stable diff independently.
