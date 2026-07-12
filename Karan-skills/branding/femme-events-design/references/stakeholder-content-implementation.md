# Stakeholder Content Implementation Pattern

Use this when Amanda/Karan provides website content via email, GitHub comment, or another stakeholder source.

## Durable lessons from Femme Events Issue 62

1. Preserve the homepage’s existing job before replacing copy.
   - The homepage 4-step process described the pre-client/public journey: Book, Plan, Design, Celebrate.
   - Amanda’s detailed 11-step timeline described what happens after a client decides to work with Femme.
   - Correct implementation: keep the 4-step homepage process, create a separate `/what-happens-next` page for the post-booking timeline, and link to it from the homepage.

2. Do not infer a gallery requirement from supplied photos.
   - Photos were provided as content inputs, but Karan did not want a homepage gallery.
   - If a photo gallery is ever requested, he expects images to be managed through Sanity Studio/CMS unless the task explicitly chooses local public assets.
   - Avoid committing image derivatives as public assets unless the PR scope names that workflow.

3. Vendor content is safer than vendor media.
   - Add high-confidence vendor names, categories, official URLs, and socials to fallback/CMS data.
   - Exclude ambiguous vendors publicly rather than guessing. For Issue 62, `Hong Kong bi chelo` was excluded because the research confidence was low.
   - Do not publish third-party logos/photos/reference assets unless permissions are confirmed.

4. PR-comment correction workflow.
   - Treat Karan’s PR comment as acceptance criteria.
   - Remove/revert the unwanted scope, not just hide it.
   - Post a PR reply that maps each comment to the concrete fix, local validation, and remote SHA verification.

## Suggested closeout wording

- "Restored homepage section to its original purpose."
- "Moved expanded post-booking flow to a dedicated page."
- "Removed homepage gallery and local photo assets; future gallery work should use Sanity-managed images unless directed otherwise."
- "Kept vendor/footer updates that were approved."
