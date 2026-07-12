# JMD testimonial native-publish live smoke pattern

Use after merging/deploying a JMD PR that removes or changes testimonial Studio visibility gates and the issue requires confirming a test testimonial is visible on non-prod.

## Pattern proven on issue #145

1. **Verify merge first**
   - Re-query the PR via REST and confirm `merged: true`, `state: closed`, `merged_at`, and `merge_commit_sha`.
   - Re-query `branches/main` and confirm the merge commit is the main head.

2. **Deploy Studio from clean main worktree**
   - Use a detached worktree at `origin/main`.
   - Run:
     ```bash
     npm --prefix studio ci
     npm --prefix studio run build
     cd studio && npx sanity deploy
     ```
   - Required success evidence: `Success! Studio deployed to https://jmd-studio.sanity.studio/`.
   - Verify hosted URL headers and `npx sanity schema list`.

3. **Inspect live testimonial state before mutation**
   ```bash
   cd <clean-worktree>/studio
   npx sanity documents query '*[_type == "testimonial"] | order(_updatedAt desc) { _id, _rev, _createdAt, _updatedAt, reviewerName, rating, quote, source, status, "isDraft": _id in path("drafts.**") }' --pretty
   ```

4. **For an existing test testimonial that is natively published but still hidden by legacy custom status**
   - Use a conservative `sanity exec --with-user-token` patch script.
   - Put the script **inside the Studio directory** (for example `<worktree>/studio/publish-jmd-test-testimonial.mjs`) so `import {getCliClient} from 'sanity/cli'` resolves against local dependencies. Running the script from `/tmp` can fail with `ERR_MODULE_NOT_FOUND: Cannot find package 'sanity'`.
   - Guard before mutation: assert `_type`, expected `reviewerName`, expected old test quote, and expected old legacy `status` so the script refuses to patch the wrong customer record.
   - Patch to valid test content, unset `status`, then read back the document.

   Example shape:
   ```js
   import {getCliClient} from 'sanity/cli'

   const client = getCliClient({apiVersion: '2025-02-19'}).withConfig({dataset: 'production'})
   const id = '<test-doc-id>'
   const before = await client.fetch('*[_id == $id][0]{_id,_type,reviewerName,quote,status}', {id})
   if (before._type !== 'testimonial') throw new Error('wrong type')
   if (before.reviewerName !== 'This is a test') throw new Error('refusing non-test doc')

   await client.patch(id)
     .set({
       quote: 'This is a test testimonial for website visibility verification.',
       source: 'manual',
       sourceLabel: 'Test review',
       rating: 5,
     })
     .unset(['status'])
     .commit({returnDocuments: true})

   const after = await client.fetch('*[_id == $id][0]{_id,_rev,reviewerName,rating,quote,source,sourceLabel,status}', {id})
   console.log(JSON.stringify({before, after}, null, 2))
   ```

5. **Verify endpoint with cache busting**
   - Request `https://jmd-non-prod.vercel.app/api/testimonials?hermes_verify=<timestamp>` with no-cache headers.
   - Confirm HTTP 200 JSON array, expected test `_id`, count, names, and no internal fields leaked (`status`, `featured`, `sortOrder`, `gbpReviewId`, `importedAt`, `approvalNotes`).

6. **Verify homepage DOM + console**
   - Browser-load `https://jmd-non-prod.vercel.app/?hermes_verify=<slug>`.
   - DOM evidence is acceptable for carousel items that may be off-screen in screenshots: check `document.body.innerText` / the `Customer reviews` region includes the test quote, reviewer name, and source label.
   - Also read browser console and confirm no JS errors.
   - Screenshot evidence should not be overclaimed if the carousel starts on earlier cards; say DOM confirmed if the card is rendered but not visually in the current viewport.

7. **Issue closeout**
   - Comment with merge SHA, Studio deploy evidence, Sanity mutation readback summary, endpoint evidence, DOM/console evidence, and any screenshot limitation.
   - Close the issue as completed only after all live ACs are verified.

## Key pitfall

Sanity's native `perspective: "published"` can return old documents that are natively published but still carry legacy custom `status: "draft"`. For native-publish migrations, do not blindly strip the old status gate unless you either migrate/unpublish legacy records or implement a transitional read rule that includes status-less native records while still excluding legacy non-`published` status records.