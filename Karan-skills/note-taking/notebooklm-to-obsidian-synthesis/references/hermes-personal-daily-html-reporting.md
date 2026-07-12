# Hermes Personal Daily HTML Reporting Pattern

Use this reference when Karan asks for a recurring end-of-day status report for `sabnanikl-dev/Hermes-personal` or another autonomy/revenue experiment repo.

## Goal

Deliver a beautiful, human-readable HTML report every evening that answers:

- What work happened today?
- How much revenue was generated today?
- Is the current product ready to deploy / approve / sell?
- Which autoresearch-style tests ran, and what decisions did they produce?
- What changed in GitHub, repo validators, cron jobs, and product artifacts?
- What is the current bottleneck or interesting signal?

## Recommended architecture

Prefer a **repo-local deterministic report generator** plus a **script-only Hermes cron**:

1. Add a repo-local script, e.g. `scripts/daily_status_report.py`.
2. The script reads only durable repo/source-of-truth state:
   - git commits for the report date;
   - Product 001 `experiment-ledger.tsv`;
   - Product 001 `revenue-ledger.tsv`;
   - launch readiness checklist;
   - approval packet status;
   - dist artifacts / product pack files;
   - local validators;
   - open GitHub issues/PRs;
   - Hermes Personal cron context.
3. Generate a self-contained HTML file outside the repo by default, e.g.
   `~/.hermes/reports/hermes-personal/daily/YYYY-MM-DD-hermes-personal-status.html`.
   This keeps scheduled reporting from dirtying the working tree every day.
4. Print a concise text summary plus `MEDIA:/absolute/path/to/report.html` so Telegram/Discord delivers the report as an attachment.
5. Schedule via a `no_agent=True` cron job so the report is deterministic, cheap, and does not spend LLM tokens.

## Revenue tracking

Add a simple product revenue ledger rather than scraping marketplace dashboards first:

```text
date	product	channel	gross_revenue_usd	net_revenue_usd	orders	refunds	notes
YYYY-MM-DD	Product Name	gumroad	0.00	0.00	0	0	Not launched / no sales logged.
```

This makes the report honest before checkout is live and gives future agents a stable place to record sales once a platform export/API is available. Do not infer revenue from vibes or approval state.

## HTML report content

Use a dashboard layout rather than a text dump:

- hero header with report date;
- metric cards for revenue, product status, readiness %, validation pass/fail;
- executive readout / interesting signals;
- revenue table;
- work-done commits table;
- product readiness by checklist section;
- deliverable artifact sizes/existence;
- autoresearch experiment table;
- validation gate table;
- GitHub state;
- active cron context;
- exact approval request on file.

For Karan, the useful executive signal is usually the bottleneck: e.g. “revenue is $0 because checkout is approval-gated,” or “product is packaged and approval-ready; next bottleneck is public listing approval.”

## Cron scheduling detail

Hermes cron script paths must be relative to `~/.hermes/scripts/`, not absolute repo paths. If the real report generator lives in the repo, create a tiny wrapper:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /Users/creator/projects/Hermes-personal
exec python3 scripts/daily_status_report.py
```

Save it as:

```text
~/.hermes/scripts/hermes_personal_daily_status_report.sh
```

Then create the cron with:

```text
schedule: 30 22 * * *
script: hermes_personal_daily_status_report.sh
no_agent: true
```

## Verification checklist

Before reporting success:

- Run the report script manually and verify it prints a `MEDIA:` line.
- Verify the generated HTML exists and contains the required sections.
- Run repo validators and `git diff --check` if adding repo files.
- Commit/push repo-local generator/ledger changes, then verify local HEAD equals remote `origin/main`.
- List the cron job back and verify name, schedule, enabled state, script, `no_agent`, delivery target, and next run.

## Boundaries

The report may read local repo state, ledgers, validators, GitHub metadata, and cron metadata. It must not publish listings, activate checkout/payment, send outreach, mutate external marketplaces, or claim revenue that was not logged or verified.
