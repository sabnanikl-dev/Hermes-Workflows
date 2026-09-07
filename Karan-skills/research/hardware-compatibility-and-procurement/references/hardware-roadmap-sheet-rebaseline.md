# Hardware roadmap sheet rebaseline

Use this when an approved hardware architecture change must be reflected in a Google Sheets shopping roadmap rather than appended as a contradictory alternative.

## Coupled surfaces

Treat these as one logical record set:

- stable item keys;
- phase, priority, and architecture tags;
- recommendation and alternative text;
- `HYPERLINK` formulas;
- compatibility, dependency, warning, and guardrail columns;
- architecture/north-star and sources/notes tabs;
- filter ranges.

A renamed row can keep a valid formula that points to the superseded product class. Deleting visible recommendation rows can also leave retired cables, trays, network fabrics, tags, or guardrails active elsewhere.

## Preflight

1. Read spreadsheet metadata and all coupled tabs.
2. Read the shopping table with `valueRenderOption=FORMULA` so formulas survive round-trip.
3. Save a temporary pre-mutation JSON snapshot.
4. Assert header width, row count, unique stable keys, and current filter ranges.
5. Classify each old architecture lane as active, prepared/optional, or retired.

Example read shape:

```bash
gws sheets spreadsheets values get \
  --params '{"spreadsheetId":"ID","range":"Shopping List!A1:R100","valueRenderOption":"FORMULA"}'
```

## Build the intended table in memory

- Map rows by stable item key.
- Remove retired-lane rows explicitly.
- Update all coupled fields for surviving rows together.
- Preserve surviving formulas exactly only when their target is still semantically correct.
- Rebase purchase-link formulas when an item is renamed.
- Blank buy links for reuse, software-only, or no-purchase decisions.
- Add a dated source/decision row stating what was promoted, demoted, and still requires separate approval.
- Rebuild architecture and guardrail tabs so they do not contradict the active shopping list.

Before writing, assert required new keys exist once, retired keys are absent, retired tags are absent, and several high-risk item-to-guardrail pairs remain aligned.

## Write, clear, and verify

- Write all replacement ranges with one values batch update using `USER_ENTERED` so formulas remain formulas.
- Clear stale tail rows after writing a shorter table.
- Reset each basic filter to the final exact row and column range.
- If any API call fails, re-fetch live state before retrying; do not assume cross-call atomicity.

Sheets omits trailing empty cells in each returned row. Pad every row to the declared schema width before exact comparison:

```python
def pad(row, width):
    return list(row) + [""] * (width - len(row))
```

Then verify from the live API:

- exact formula-view table equals the padded intended table;
- final row count and tag/priority totals;
- required keys appear exactly once;
- retired keys and architecture vocabulary are absent from active rows;
- architecture and source decision rows are present;
- filter endpoints match the final table;
- renamed rows' links target the new product class;
- reuse/no-purchase rows have no stale buy links;
- guardrail text remains attached to the correct item.

## Common semantic-drift traps

- Renaming `12U rack` to `24U rack` while preserving the old 12U search formula.
- Removing compute nodes but leaving their fabric cables, trays, NICs, or storage-format assumptions active.
- Leaving old rows below a shorter rewritten table.
- Treating a successful values write as proof that filters and tail rows were fixed.
- Diagnosing Sheets' omitted trailing blanks as a real content mismatch instead of padding first.

Report the final spreadsheet URL, row count, added/removed keys, formula count and intentional formula removals, retired-vocabulary scan, filter verification, and API readback result.
