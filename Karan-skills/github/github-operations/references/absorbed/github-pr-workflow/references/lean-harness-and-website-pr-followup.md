# Lean Harness + Website PR Follow-up Pattern

Use when Karan asks to "submit that PR and any PR you deem necessary" after a repo/process audit.

## Pattern

1. Reconstruct state for every involved repo separately:
   - `git fetch origin main --prune`
   - `git checkout main && git pull --ff-only origin main`
   - `gh pr list -R OWNER/REPO --state open`
2. Convert the audit's recommended changes into the smallest safe PR set.
   - Template/process repo: one lean docs PR only; keep it class-level and generic.
   - Product/site repo: open only PRs whose prerequisites are satisfied.
3. Do not overrun sequencing:
   - If issue B depends on issue A being merged, either stack explicitly or wait.
   - If a later issue needs merged assets/SEO/QA evidence, do not open it early just to appear proactive.
4. For template PRs, verify newly added text does not leak project-specific names, IDs, or local-agent assumptions. Check added diff lines, not the whole file, because the template may already contain generic warnings such as "do not add Linear issue IDs".
5. For site asset PRs, copy only referenced/approved assets, record source path + size + approval status + hash, and verify every HTML `assets/...` reference resolves locally.
6. For conservative SEO/JSON-LD PRs, parse JSON-LD locally and assert unverified fields are absent (`telephone`, `address`, `geo`, `sameAs`, `image`, `openingHoursSpecification`, ratings, price/commerce fields, URL/canonical if the domain is unapproved).
7. After each push, independently verify the PR:
   - `gh pr view N -R OWNER/REPO --json url,state,mergeStateStatus,headRefOid,headRefName,baseRefName,commits,files`
   - `git ls-remote https://github.com/OWNER/REPO.git refs/heads/<branch>`
   - Require the remote branch SHA to match `headRefOid` before reporting.
8. Check `gh pr checks`; if the repo has no checks, say "no checks reported" rather than implying CI passed.

## Pitfalls

- A repo-wide grep for project-specific words can false-positive on template guardrails. Use `git diff -U0 | grep '^+'` to check only newly added lines.
- Opening final QA/handoff PRs before asset/SEO PRs merge creates stale evidence. Keep those issues for the end.
- Do not merge unless Karan explicitly asked to merge; "submit PR" means open and verify PRs, not merge them.
