# Hermes-personal Product Pack Launch Assembly Pattern

Use after a Hermes-personal passive/low-fulfillment revenue review converges on “stop researching; assemble the product and approval packet.”

## Trigger

Karan approves proceeding from a review/synthesis into a repo-local launch-readiness build for `sabnanikl-dev/Hermes-personal`, especially Product 001 or a similar digital product pack.

## Core lesson

For the revenue experiment, a strong harness is not enough. Once source evidence, safety gates, and product drafts are in place, the next useful artifact is a buyer-facing deliverable plus a single approval surface. Avoid adding more rubrics, NotebookLM loops, or validators unless they directly protect the buyer-facing artifact.

## Recommended build contract

1. Ground current repo state before mutating:
   - `git fetch origin main --prune`
   - `git status --short --branch`
   - verify local `HEAD` matches `origin/main`
2. Read the repo-local product skills and active product files:
   - `skills/manifest.md`
   - `skills/ai-money-product-research/SKILL.md`
   - `skills/product-experiment-loop/SKILL.md`
   - active product `README.md`, `brief.md`, `source-map.md`, `prompts.md`, `workflow-blueprint.md`, `validation-checklist.md`, `revenue-recovery-calculator.md`, `landing-copy-draft.md`, `sample-posts-for-approval.md`, `launch-approval-packet.md`, and launch tracker.
3. Create a deterministic repo-local assembler, typically `scripts/build_product_pack.py`, using stdlib-only Python when possible.
4. Produce buyer-facing artifacts under the product `dist/` directory:
   - canonical Markdown;
   - print-ready HTML;
   - PDF if a local converter/headless browser is available without installing heavy/paid dependencies.
5. The assembled product should combine and prune into one coherent buyer artifact:
   - intro / who it is for;
   - source-backed buyer brief;
   - hypothesis calculator, not a promise;
   - workflow blueprint;
   - validation checklist;
   - prompt pack;
   - source appendix;
   - claim-safety notes.
6. Add an automated leak check over `dist/` that fails on internal text such as approval banners, owner names, local paths, repo paths, Telegram instructions, agent emails, and internal filenames.
7. Fill `launch-approval-packet.md` as the single decision surface:
   - final title;
   - buyer segment;
   - platform recommendation;
   - one price, not a menu of options;
   - refund policy;
   - deliverable paths;
   - evidence summary;
   - claims included/excluded;
   - exact public-live action;
   - exact approval request Karan can reply `approve` to.
8. Update launch readiness and the experiment ledger honestly. Ledger rows for packaging are proxy/readiness signals, not market demand.
9. Validate, commit, push, and verify remote `origin/main` SHA before reporting.

## Validation bundle

Run the product assembler and all repo gates:

```bash
python3 scripts/build_product_pack.py
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

After push:

```bash
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git ls-remote origin refs/heads/main | awk '{print $1}')
test "$LOCAL" = "$REMOTE"
gh api repos/sabnanikl-dev/Hermes-personal/branches/main --jq '{sha: .commit.sha, message: .commit.commit.message}'
```

## External approval boundary

Repo-local assembly, package generation, approval packet drafting, and direct commit/push are allowed only within the explicitly authorized Hermes-personal autonomy scope. Do not publish listings, activate checkout/payment/waitlists, post publicly, send outreach/DMs, buy tools/domains, or make ROI/revenue/compliance claims without Karan’s explicit Telegram approval.

## Builder-lane pitfall

Claude Code or another builder lane can silently stall after creating partial files. Do not immediately call that a success or a failure. Inspect process state, worktree status, generated files, and logs. If the builder remains idle with no stdout and only partial repo-local artifacts, it is acceptable to salvage the partial artifact and finish directly only when the task already has explicit repo-local autonomy/approval. Disclose the fallback in the final report; do not claim a clean builder-lane pass.
