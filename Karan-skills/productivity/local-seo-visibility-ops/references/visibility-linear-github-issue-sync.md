# Visibility Linear ↔ GitHub Issue Sync

Use when a local SEO / visibility plan is tracked in Linear but part of the work belongs in a website repo or another implementation repo.

## Decision rule

Mirror a Linear visibility issue into GitHub only when the work needs repo-side execution, branch/PR tracking, cross-QA, or reviewable website/code artifacts.

Good GitHub mirrors:

- Local service page implementation, e.g. `/atlanta-wedding-coordinator`.
- Website analytics/conversion instrumentation.
- Metadata/schema/sitemap/route implementation.
- Repo-owned docs or reusable templates that will be changed by PR.

Usually keep Linear-only:

- GBP/profile edits, category decisions, photos/media uploads, Q&A, LocalPosts.
- Review request outreach and review replies.
- Directory account creation/submissions.
- Credential/access/account setup decisions.

If a GitHub issue already owns the repo-side concern, do not create a duplicate. Comment on the existing GitHub issue with the Linear source issue and add a Linear comment linking the GitHub issue/comment.

## Sync pattern

1. Read the Linear project/issue list first; find relevant parent and child issues.
2. Search open GitHub issues in the target repo for matching route/feature/measurement terms and Linear identifiers.
3. For Linear issues that need repo work:
   - Create or update a GitHub issue.
   - Link the Linear issue and parent project in the GitHub body.
   - Include baseline metrics/strategy context only as much as implementers need.
   - State the approval boundary: issue creation does not approve merge/deploy/account mutation.
4. Comment back on the Linear issue with the GitHub issue URL and scope.
5. If an existing GitHub issue was reused, comment there and comment back in Linear with the GitHub comment URL.
6. Verify mutations by reading back:
   - GitHub issue number/title/body or comment contains the Linear ID and key context.
   - Linear direct comment lookup by `comment(id:)` when possible, not only `comments(last:1)`.

## GitHub issue body essentials

- Linear source issue URL and parent/project URL.
- Why this work matters for the visibility goal.
- Exact repo-owned scope.
- Out-of-scope live-account/public mutations.
- Acceptance criteria and verification commands.
- Workflow reminder: branch → PR → cross-QA → human approval → verified merge/deploy.

## Pitfalls

- Do not mirror every Linear visibility issue into GitHub; live ops/account/public mutation work usually stays Linear-only.
- Do not create a duplicate GitHub issue when an existing analytics/SEO/route issue already owns the repo-side work.
- Do not treat a GitHub issue as permission to publish, deploy, merge, mutate GBP, or send outreach.
- Do not let Linear become the coding queue when the user's workflow preference is GitHub branches/PRs for implementation.
