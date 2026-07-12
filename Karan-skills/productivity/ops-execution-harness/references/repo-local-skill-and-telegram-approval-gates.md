# Repo-local skill + Telegram approval gates

Use this reference when a project/repo needs its own local operating skill, not a globally installed Hermes skill.

## Pattern

For repo-specific autonomous experiments, create a local skill folder inside the repo:

```text
skills/
  manifest.md
  <class-level-local-skill>/
    SKILL.md
```

This local skill should be read by agents working in that repo, but it should not be installed into the global Hermes skill library unless the workflow generalizes beyond the repo.

## When this is appropriate

- The autonomy should apply to one repo only.
- The repo has a specific experiment or product loop.
- Agents need detailed repo-local operating rules, sources, prompts, or approval gates.
- The user wants faster autonomous progress without widening global/profile authority.

## Recommended repo files

```text
AGENTS.md
skills/manifest.md
skills/<local-skill>/SKILL.md
docs/<approval-or-policy>.md
prompts/<scheduled-agent>.md
scripts/<local-skill-or-loop-audit>.py
products/<product-slug>/
```

## Approval gate pattern

For external setup/publication workflows:

1. Let agents do repo-local work autonomously.
2. Let agents prepare non-public external setup using agent-owned accounts when explicitly allowed.
3. Stop before anything public-live.
4. Send the final approval request to the user's current origin chat, phrased so the user can reply `approve`.

Approval request shape:

```md
Approval requested: <one-line action>

What will go live:
- ...

Account/platform:
- ...

Public URL or draft target:
- ...

Claims included:
- ...

Risk/caveat:
- ...

If approved, I will:
- ...
```

## External setup rule

If the user says to use agent-owned accounts instead of personal accounts, encode the specific account identity in the repo-local policy and cron prompt. Example:

```text
Default setup account: karanagent20@gmail.com
Approvals: current Telegram origin chat
Public-live gate: posts, listings, checkout/payment links, outreach, paid plans, and claims
```

Do not require the user to perform platform work unless blocked by CAPTCHA, phone verification, tax/bank/KYC, credentials, or paid-plan decisions.

## Deadline sprint cadence

If the user sets a near-term launch/publication deadline for the repo-local experiment, encode it in the harness rather than only in chat:

1. Add a dated decision record with the target date and launch criteria.
2. Add a product launch-readiness tracker under the active product workspace.
3. Update the repo-local skill and scheduled-agent prompt so deadline work outranks generic improvements.
4. Keep the normal scout cadence, then add a temporary high-frequency sprint cron with a finite repeat count.
5. Add a one-shot final approval-packet cron for the target day.
6. Preserve the same public-live gate: faster cadence accelerates preparation, not authority to publish.

Useful cadence shape:

```text
normal product scout: 3–5 times/day
launch sprint: every 60–90 minutes until deadline, finite repeat count
final approval packet: one-shot on target morning
```

## Validation

Add or update repo-local audit scripts so they assert:

- the local skill exists;
- the approval policy exists;
- the account identity appears in the local skill/policy;
- the current-origin approval channel appears in the local skill/policy;
- the deadline decision/tracker exists when a deadline is active;
- scheduled prompts include the policy, deadline, and approval language;
- context/scout scripts include the local skill, policy, and deadline files.

Run the repo's validators and any focused ad-hoc verification after changing these scripts.
