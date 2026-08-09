# Owner-approved source before builder launch

Use this pattern when an implementation issue requires owner-, client-, legal-, or compliance-reviewed source material before public copy or behavior may be added.

## Separate the authorities

Do not collapse these into one approval:

1. Approval of an operational policy.
2. Approval to orchestrate or work the issue.
3. Approval of exact public-ready source text.
4. Approval to deploy, activate, publish, or mutate live systems.

“Work on the issue” does not create the missing source. If the acceptance contract says the public artifact may exist only after source approval, launching a builder that must invent it produces either fabricated evidence or a knowingly non-merge-ready PR.

## Pre-builder check

Read the live issue, its comments, linked tracker policy, and current repository. Search for an existing source record and approved text.

A qualifying source packet should contain:

- exact approved text or data;
- approver name or role;
- approval date;
- intended effective date where relevant; and
- the scope of authority granted.

If any required item is absent, stop before the builder lane and report the exact gate.

## Draft-for-approval lane

If the human asks for help obtaining approval:

1. Create a clearly labeled draft, not implementation evidence.
2. State that it is not approved, published, or legal advice.
3. Ground it in both current implementation and approved future contracts; do not silently describe planned behavior as already active.
4. Include a copy-ready approval block that captures every metadata field the implementation issue requires.
5. State which downstream actions remain separately gated.
6. Resume the builder only after the approval is returned and recorded on the authoritative issue/tracker surfaces.

## Analytics/privacy copy pitfalls

- An approved analytics policy is not approval of public privacy wording.
- Do not invent legal conclusions, retention periods, consumer-rights promises, or data-sale claims.
- Do not make an absolute “no query strings” statement if a bounded attribution contract permits a complete pre-approved UTM tuple.
- If policy approves a future measurement that the production-disabled runtime does not yet ship, phrase it prospectively and require activation implementation to reconcile with the approved source before collection begins.
- Copy approval alone does not authorize deploy, DNS, consent-platform changes, analytics activation, account mutation, or live collection.
