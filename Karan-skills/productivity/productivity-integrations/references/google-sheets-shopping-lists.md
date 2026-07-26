# Google Sheets shopping lists: reusable playbook

## Sheet shape

Use two tabs:

1. **Shopping List** — filterable, frozen header.
2. **Sources & Notes** — price/compatibility citations, date checked, and decision rationale.

Recommended Shopping List columns:

```text
Phase | Category | Priority | Item | Recommended Buy | Cheaper Alternative |
Premium Alternative | Target Price Range | Recommended Link | Cheaper Link |
Premium Link | Buy Trigger / Notes
```

Use `=HYPERLINK("URL", "Label")` for link cells so the sheet remains legible.

## Update protocol

1. Read the target tab with `valueRenderOption='FORMULA'` before writing.
2. Identify rows by stable **Item** labels, not row numbers; row numbers change after removals.
3. On a user revision, remove superseded items and replace conflicting rows in place. Optional choices should be named `Optional ... pivot` and placed beside the default item.
4. Clear/rewrite the bounded table only if needed to preserve coherent phase ordering; then reset the filter range.
   - If dependent annotations, formulas, or audit columns live to the right of the rewritten range, rebuild or clear those columns in the same mutation. Deleting/renaming rows in `A:L` while leaving `M:Q` untouched silently shifts compatibility notes onto the wrong items.
   - Rebuild dependent columns by stable item/record key, never by the prior row order.
5. Read back and assert:
   - expected row count;
   - required new/replaced item labels exist;
   - intended removed labels are absent;
   - source-note topics exist;
   - several known item → annotation/formula pairs still align after any row deletion, insertion, or rename;
   - filter ranges cover the full final table width and row count.
6. If the file is created under an agent OAuth owner, share only with the explicitly known owner/collaborator and verify Drive permission readback.

## Hardware compatibility checklist

Before listing an item as a purchase recommendation, cite primary product specs and compare actual dimensions/limits:

- **Case ↔ cooler:** max cooler height, including whether a retainer/rail changes clearance.
- **Case ↔ GPU:** max length, width, thickness/slot clearance, and whether front fans/radiator installation changes those values.
- **Motherboard ↔ RAM:** exact memory generation, DIMM capacity support, QVL/BIOS condition, and low-profile clearance if the CPU cooler overlaps RAM.
- **Motherboard ↔ M.2:** PCIe generation/lane source per slot and each slot’s supported physical lengths.
- **SSD form factor:** desktop defaults to 2280 unless a shorter form factor is required. 2230 may physically require a length adapter even when electrical NVMe support exists. 2242/2260 can be board-supported but have less selection and worse price-per-TB.
- **Storage tradeoff:** HDDs are a legitimate budget model/dataset archive; keep boot/active-model/cache workload on NVMe and state the load-speed compromise explicitly.

## 4U rackmount pitfall

“4U” is not a sufficient fit claim. Manufacturer specs can have different clearances with a GPU expansion-card retainer installed vs. removed. Record the exact condition in the sheet. If choosing a cooler that only fits with the retainer removed, do not also assume the chassis provides integrated GPU anti-sag support; record the tradeoff and exact GPU dimensions to verify before purchase.

## Price guidance

- Treat prices as current, volatile ranges rather than promises.
- Prefer direct manufacturer pages for dimensions/compatibility; use reputable retail or search pages for purchasing.
- State buy triggers for expensive parts (e.g., buy near a target price, only after workload saturation, or only after thermal/network measurements prove a bottleneck).
