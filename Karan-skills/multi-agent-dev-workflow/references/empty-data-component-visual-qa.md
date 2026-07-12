# Empty-data component visual QA with temporary local fixture data

Use this when a frontend PR intentionally ships an empty public data artifact (for honesty/public-safety) but the human needs screenshots of the populated UI state before merge.

## Pattern

1. **Do not change the PR branch to fake data.** Keep committed data honest (for example `window.JMD.testimonials = []` until records are approved/published).
2. **Create a disposable preview copy** outside the repo/worktree, e.g. under `/tmp/<repo>-visual-preview/`.
3. Copy the static site/build output into that disposable directory.
4. Override only the local preview data artifact in that disposable copy with clearly labeled `TEMPORARY LOCAL VISUAL-QA DATA ONLY` sample records.
5. Serve the disposable directory over localhost and capture screenshots against the populated UI state.
6. Disclose in the user-facing report that screenshots use temporary local fixture data and that the PR itself still ships the honest empty/no-data state.
7. After screenshots, stop the server and re-run the repo’s canonical verification command from the real PR worktree. This avoids stale-verification warnings caused by temp files or prompt files written during orchestration.
8. Confirm the real worktree is clean and, when relevant, compare the committed data artifact with the temp preview artifact so it is obvious sample data did not leak into the PR.

## Why

Some public-safe features (testimonials/reviews, curated feeds, approved customer content) must not ship fake visible content. But visual inspection of the populated card/carousel state is still valuable. A disposable preview copy lets agents exercise the UI without contaminating the PR.

## Pitfalls

- Do **not** write local fixture data into the repo’s real `site/assets/...data.js` unless the PR explicitly owns generated approved content.
- Do **not** claim “fully verified” after creating screenshots or temp files until the canonical repo verification has been re-run afterward.
- Do **not** leave a tracked background preview server running after reporting screenshots.
- Label sample card text as visual-QA-only so screenshots cannot be mistaken for approved customer copy.
