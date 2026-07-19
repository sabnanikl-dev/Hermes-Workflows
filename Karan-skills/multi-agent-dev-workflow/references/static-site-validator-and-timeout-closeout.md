# Static-site validator PR + timeout closeout lessons

Session-derived pattern from a JMD static-site PR where the Claude builder timed out in Hermes after 600s, but had already committed, pushed, and opened the PR.

## Durable lessons

### 1. Treat a builder CLI timeout as an unknown state, not an automatic failure

If `claude --print` / another builder exits through the orchestrator timeout, immediately inspect side effects before restarting or rebuilding:

```bash
git status --short --branch
git log --oneline -5
gh pr list --head <branch> --json number,title,url,state,headRefOid
```

If a commit/PR already exists, continue from verified GitHub state instead of launching a duplicate builder. Verify local `HEAD` matches the PR `headRefOid` / commit list before reporting.

### 2. Preserve validator negative-test proof

For static-site regression checks, positive `npm test` is not enough. Add at least one focused negative mutation that proves the new check catches the intended missing/unsafe condition, then restore the file and re-run the validator:

- remove the required block/marker -> validator fails;
- remove one required link/field -> validator fails;
- inject forbidden public-safety language -> validator fails;
- restore original file -> validator passes and `git status` is clean.

Use a small Python script with `try/finally` so the file is restored even if a negative assertion fails.

### 3. Avoid comment false positives in regex-based HTML checks

When a static check keys off a marker attribute or link, match the attribute inside an actual opening tag, not anywhere in the fragment. Comments frequently document complete marker/link markup and can poison a bare string or raw-tag search.

Good marker check:

```js
new RegExp(`<section\\b[^>]*\\bdata-article-cta\\b[^>]*>`, "i")
```

Risky marker check:

```js
html.search(/\bdata-article-cta\b/)
```

For a regex-based structural/link validator, strip non-rendered comments **before** extracting `<main>`/`<section>` regions or matching anchors:

```js
function stripHtmlComments(html) {
  return html.replace(/<!--[\s\S]*?-->/g, "");
}

const main = mainBody(stripHtmlComments(homepageHtml));
const feature = sectionById(main, "feature-id");
const hasRequiredLink = linksTo(feature, "target-route/");
```

Stripping first also prevents a commented `</main>` or `</section>` from truncating a non-greedy region extractor. Add a deterministic self-test that proves both sides of the regression:

- the old raw matcher accepts a commented-only CTA (expected red / documents the bug);
- the comment-stripped matcher rejects it;
- a real CTA still passes;
- mixed real + commented markup passes because of the real CTA;
- cover both the dedicated-section path and any broader contextual-`<main>` path.

Do not generalize this into “regex can parse arbitrary HTML.” Keep the validator scoped to repo-controlled static markup with documented non-nesting assumptions; use a parser when nested/irregular HTML breaks those assumptions.

### 4. Use local browser evidence even for static repos

For static HTML/CSS PRs, start a tracked local server (`python3 -m http.server --directory site`), verify HTTP 200, inspect browser console, and use DOM measurements for CTA/link layout. If the browser tool cannot resize the viewport directly, a same-origin iframe with a fixed width can provide a cheap responsive measurement:

```js
new Promise((resolve) => {
  const f = document.createElement('iframe');
  f.src = location.href;
  f.style.cssText = 'width:375px;height:900px;border:0;position:absolute;left:0;top:0;z-index:-1;';
  f.onload = () => {
    const d = f.contentDocument;
    resolve({
      scrollWidth: d.documentElement.scrollWidth,
      clientWidth: d.documentElement.clientWidth,
      links: [...d.querySelectorAll('[data-article-cta] a')].map(a => {
        const r = a.getBoundingClientRect();
        return { text: a.textContent.trim(), width: r.width, height: r.height, x: r.x, y: r.y };
      })
    });
  };
  document.body.appendChild(f);
});
```

Report this honestly as DOM/layout measurement, not a full Playwright pass.

### 5. Reviewer launch quoting

For reviewer runs that need a per-process reviewer token and a long prompt, prefer writing a tiny wrapper script and prompt file over embedding command substitution/token assignment inside a one-liner. This avoids shell quoting/redaction surprises while keeping the token scoped to the subprocess.

```bash
#!/usr/bin/env bash
set -euo pipefail
TOKEN="$(/usr/bin/security find-generic-password -s hermes-codex-reviewer-github-token -a codex-reviewer -w)"
GH_TOKEN="$TOKEN" codex exec --cd /path/to/worktree --dangerously-bypass-approvals-and-sandbox "$(cat /tmp/review-prompt.md)"
```
