# Exact-head before/after copy-review reports

Use this pattern when a user wants to personally review public prose changes without reading a full code diff.

## Output contract

Produce one self-contained HTML file that:

- names the exact base and head revisions;
- includes every reader-facing prose change exactly once in the main card inventory;
- separates visible copy, search/social metadata, structured data, and runtime-generated reader text;
- excludes developer-comment-only edits and non-prose implementation/evidence changes;
- shows plain-language **Before** and **After** panels with token-level removal/addition highlighting;
- groups cards by page and labels the surface (hero, heading, body, metadata, FAQ, runtime message, related-links copy);
- provides page navigation, text search, useful filters, print CSS, and locally persisted review checkboxes;
- elevates meaning-sensitive edits such as removed qualifiers, changed prices/timelines, new claims, and deleted copy into a decision-hotspot section;
- states what is excluded and preserves approval/merge/deploy boundaries.

## Source extraction

1. Freeze `base` and `head` SHAs before extraction.
2. Generate a scoped unified diff over the public-copy files; hash the diff and record the digest in the report.
3. Parse changed runs by hunk, tracking old/new line numbers.
4. Convert each run into reader text according to its surface:
   - HTML text nodes: strip tags and decode entities;
   - description/OG/Twitter metadata: extract and decode `content`;
   - JSON-LD/structured FAQ answers: extract the rendered answer string;
   - reader-visible runtime strings: extract the assigned text;
   - HTML comments: exclude unless the user explicitly asks for implementation commentary.
5. Preserve deletions with an explicit “Removed entirely” after-state.
6. Do not collapse repeated copy across different surfaces: a visible FAQ answer and its JSON-LD twin are distinct review locations.
7. Count the extracted inventory deterministically by page and surface; verify those counts against the final HTML.

## Independent acceptance accounting

Do not accept the report from displayed totals or DOM-card count alone. Independently parse the unified diff into contiguous edit runs: start at the first `-` or `+` line and end at context, hunk, or file boundaries. Preserve `(file, old_start, new_start)` and classify comment-only runs separately, inspecting the entire run for multi-line comments.

Extract the same tuple from every review card and compare multisets:

- missing tuples prove omitted reader-facing changes;
- extra tuples prove invented cards;
- multiplicity greater than one proves duplicate representation;
- `reader-facing edit runs == unique cards` proves location-level closure.

This line-reference method is stronger than DOM-node comparison when a changed run contains only one line from a larger paragraph. Then prove text fidelity per matched run using surface-aware extraction: decoded visible HTML, decoded metadata `content`, parsed JSON-LD string values, and JavaScript runtime string literals. Compare rendered panel strings rather than individual highlight nodes so inline `<mark>` wrappers cannot hide punctuation-spacing errors. Treat a visible FAQ and its identical structured answer as separate locations when their source references differ. For complete deletion, compare the before text and require an explicit UI-only empty state such as `Removed entirely`.

For repeated qualifier decisions, count removals and additions directly in diff lines, search final source scope for survivors, and require every decision-table row to match and link to one unique qualifying card.

## Prioritization

Use three review levels:

- **Owner decision**: qualifier removal, stronger promise, claim change, price/timeline/availability wording, legal/privacy or commerce meaning.
- **Read closely**: substantive rewrite, replacement framing, or complete deletion.
- **Light edit**: punctuation-focused or close wording edit.

Never infer that a small textual diff is low-risk. Removing one word such as “typically,” “minimum,” “prefer,” or “and up” can materially strengthen a promise.

## Rendering and verification

Before delivery:

1. Assert file size is nonzero and expected page/card/control counts match.
2. Serve over local HTTP; verify HTTP 200 and fetched structure.
3. Render fixed desktop and mobile viewports and visually inspect hierarchy, clipping, legibility, stacked before/after cards, and controls.
4. For very tall reports, do not rely on one giant full-page screenshot: browser/image pipelines can tile, duplicate, crop, or downscale extremely tall captures. Use a top viewport plus representative body/card captures, with explicit scroll when available, and pair them with DOM geometry/count assertions.
5. Check interactive filters/checklist behavior when browser automation is available: exercise every filter, search and no-results behavior, local persistence, clear, and progress; compare visible results with declared category totals. If automation is unavailable, do not overclaim that interaction testing occurred.
6. Record browser requests and inventory non-fragment links, external `src`/`action` attributes, forms, outbound APIs, and secret-like values. A self-contained private packet should make no external request unless explicitly intended.
7. Prove narrow-viewport semantics with geometry plus visual review: no page-level overflow, stacked comparisons, usable controls, and bounded internal scrolling for deliberately wide tables.
8. Prove print output by generating a real PDF and extracting its text. When review constraints prohibit file mutation, keep the PDF in memory and pipe it to `pdfinfo -` and `pdftotext - -`; assert required section bodies, provenance, final cards, and deletion markers.
9. Verify the final artifact still names the frozen base/head and source-diff digest, re-hash it at closeout, and confirm reviewed files and worktree state did not change.
10. Deliver the actual `.html` file, not only screenshots or a prose summary.

## Returned decision packet ingestion

When the owner sends the completed HTML back, treat that exported file—not browser history, a screenshot, or the original blank report—as the product-decision source:

1. Open the returned file in a real browser so its embedded state initialization runs; independently count all cards, approved IDs, and rejected/unchecked IDs, and verify the totals reconcile.
2. Record the decision semantics from the artifact. If unchecked can still mean “not reviewed,” stop for clarification; only convert it into a rejection ledger when the owner explicitly defined that meaning.
3. Map every rejected card to its page, source location, surface, before text, and current after text. Freeze approved cards as a no-drift set and give the builder only the rejected locations plus source-backed constraints.
4. For subjective copy repair, a changed string is not automatically a closed decision. Before reviewer fan-out, read every replacement in surrounding page context and reject mechanical substitutions that remain awkward, explain an obvious fact, narrate site taxonomy, add irrelevant setup, or preserve the same artificial frame with one token removed.
5. Use one bounded corrective pass for misses from the same owner ledger rather than reopening approved copy or starting an unbounded taste loop.
6. If the affected page bytes are inputs to revision-bound screenshots, browser evidence, or generated reports, commit the copy first, regenerate producer-owned evidence against that commit, and verify local/remote/PR head equality before exact-head reviewers run.

The final handoff should preserve both layers of evidence: the owner’s exported decision packet and the source/evidence commits that implement it. Owner approval resolves taste for the approved set; it does not replace factual-source checks, deterministic validators, or merge authority.

## Report framing

The report is a private decision aid unless explicitly approved otherwise. It must not imply copy approval, PR merge approval, publication, deployment, or client delivery. State unresolved human gates prominently and neutrally.
