# Quiet price-watch cron pattern

Use this for a recurring deal watcher that must alert only on a qualifying offer, especially when the requested destination is Telegram.

## Why a script-only cron wrapper

An LLM-driven cron run always produces a final response, which can create noisy daily “no deal” messages. Use a `no_agent: true` cron job whose script:

1. Runs a one-shot Hermes web-research query (`hermes chat -q ... --toolsets web --quiet`).
2. Requires the researcher to return either one machine-parseable deal line or `NO_ALERT`.
3. Emits a human-facing alert only when the deal line validates; otherwise emits **empty stdout**. The scheduler treats empty stdout as silent.

Use a structured line such as:

```text
NVME_DEAL|<tier>|<product>|$<price>|<retailer>|<direct purchase URL>|<stock/condition note>
```

Filter output with a strict parser/regex before delivering. Suppress command failures rather than presenting an unverified pseudo-deal.

## Deal-search prompt rules

Give the agent explicit tier order and price bands. It must:

- Search broadly rather than restricting itself to a pre-existing list of merchant links.
- Search every item in a tier and choose the lowest verified qualifying result before falling through to the next tier.
- Verify a **direct product/purchase page**, visible USD price, condition, and in-stock/buyable state; search snippets, trackers, reviews, categories, and stale caches are not enough.
- Exclude marketplace, used, refurbished, open-box, auction, membership-only, coupon-only, and bundle-only listings unless the user explicitly allows them.
- Include mandatory shipping when shown; label tax as pre-tax when it cannot be known.
- Never purchase, add to cart, or log in.

## Telegram delivery

When the user names Telegram rather than the current conversation, discover the configured Telegram home destination with `hermes status --all` and set cron delivery to `telegram:<chat_id>`. Do not use `all`, which can fan the alert into unrelated channels.

## Verification

Before creating the job, run the script once in the terminal. Confirm it produces either:

- exactly one human-ready purchase alert, or
- empty stdout when no deal qualifies.

Then create the cron with `no_agent: true`, the script name, explicit Telegram delivery, and the agreed morning schedule. Verify the returned job ID, enabled state, schedule, destination, and next run time. Keep the watcher logic and its prompt as separate files under `~/.hermes/scripts/` so the criteria can be changed without rewriting shell quoting.
