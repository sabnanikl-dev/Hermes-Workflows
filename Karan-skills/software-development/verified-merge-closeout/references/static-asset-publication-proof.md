# Static-asset publication proof after an approved merge

Use for favicon/manifest/logo/social-card releases when the question is whether the reviewed assets reached production. This verifies publication; it is not a method for forcing or proving search-engine adoption.

## Proven sequence

1. Complete exact-head merge verification first; capture the resulting merge SHA.
2. Read GitHub deployments filtered by that SHA. Select the Production environment and read that deployment's statuses. A feature-preview success is not production evidence.
3. Load the canonical public website. Record live icon/manifest link URLs, sizes, and structured-data logo URLs as applicable.
4. Fetch each scoped asset from the canonical host. Record final URL, status, MIME type, SHA-256, and comparison result. Detect HTML fallback responses rather than treating any HTTP 200 as success.
5. Obtain expected bytes from Git objects, not a potentially stale/dirty local checkout:

```js
const expected = execFileSync('git', ['show', `${merge}:public/${file}`], {cwd: repo});
const response = await page.request.get(new URL(file, canonicalBase).href);
const actual = await response.body();
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const matchesMerge = sha256(actual) === sha256(expected);
```

Require `response.status() === 200`, an appropriate content type, and `matchesMerge`. For ICO, `image/vnd.microsoft.icon` is a valid observed type; PNG uses `image/png`, and web manifests may use `application/manifest+json` with a charset parameter.

6. Save a project-owned JSON evidence artifact including merge SHA, observation time, deployment identity, declarations, and per-asset checks. Keep transient rollout state out of the knowledge vault.

## Scope of the result

- Matching bytes connect already-reviewed pixel/alpha evidence to the deployed files without regenerating them.
- DOM declarations establish what the page advertises, not native browser-tab presentation.
- A parsed JSON-LD `logo` field is not a Rich Results or Schema validator pass.
- A deployment pass, direct favicon response, or Google favicon-cache endpoint is not proof of the icon appearing on an actual Google search result. That requires direct observation of the result surface; otherwise keep the claim unverified.
- Preserve source-versus-consumer distinction in the final reply: merged, branch deleted, production verified, consumer visibility separately observed or unverified.

## Validated case

Femme Events PR #160 used this pattern after squash merge: production deployment was tied to the merge, and eight icon/manifest responses returned 200 with appropriate MIME types and bytes equal to the merged Git objects. This established publication only; no successful Google result observation was obtained. No failed search-access sequence is prescribed here as a recovery workflow.
