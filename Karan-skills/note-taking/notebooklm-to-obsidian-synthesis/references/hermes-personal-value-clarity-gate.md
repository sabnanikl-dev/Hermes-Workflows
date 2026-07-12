# Hermes-personal value-clarity gate

Use this reference when Hermes-personal passive-revenue/product-pack work reaches a packaged/approval-ready state but Karan says the value, use case, buyer, or usefulness is not clear.

## Trigger signals

Treat any of these as stop-the-line product feedback, not as a copywriting nit:

- Karan is not ready to approve public-live action.
- Product value is not obvious.
- It is unclear what the product would be used for.
- It is unclear who the product helps.
- The artifact feels self-referential, like a product about the Hermes experiment rather than a useful buyer tool.

## Required response pattern

1. **Acknowledge the distinction:** packaging/readiness is not market clarity.
2. **Remove active public-live approval pressure:** do not ask again for Gumroad/listing/checkout/post approval while the blocker is open.
3. **Mark launch state as not ready:** update approval/readiness artifacts so future agents do not treat a prior packet as valid.
4. **Capture a value-clarity blocker:** create or update a repo-local blocker file such as `products/<slug>/value-clarity-reset.md`.
5. **Redirect autonomous runs:** pause final launch-approval cron jobs and update sprint/product-scout prompts toward buyer clarity, use-case clarity, a practical walkthrough, and self-reference removal.
6. **Log the feedback as an experiment:** add an autoresearch-style ledger row with decision `blocked` or `retest`; user confusion is valid evidence.
7. **Validate and push repo-local changes:** run the repo gates, commit, push, and verify remote SHA.

## Four-line clarity test

Before a product can return to approval-ready status, it should pass this test in plain buyer language:

```text
I am: <specific buyer>
I have: <specific situation/problem>
This helps me: <specific use/action>
So I can: <specific outcome or decision, without guarantees>
```

If those lines are fuzzy, the product is not ready.

## Better next actions than launch approval

Ask for or autonomously produce one of these instead:

- one primary buyer segment;
- a concrete job-to-be-done/use case;
- a “use this in 30 minutes” walkthrough that produces a useful output;
- a buyer-facing rewrite with internal Hermes/experiment framing removed;
- a decision to hold, retest, pivot, or kill the product direction.

## Pitfall

Do not respond to this kind of critique by polishing listing copy or making the approval request more persuasive. The problem is product clarity. Treat it as a product strategy failure until the buyer/use case is obvious.