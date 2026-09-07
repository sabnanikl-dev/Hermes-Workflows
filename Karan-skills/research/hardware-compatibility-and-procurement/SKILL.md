---
name: hardware-compatibility-and-procurement
description: Use when checking hardware fit or buying used computers.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Hardware, Compatibility, Procurement, Refurbished]
    related_skills: [research-workflow]
---
# Hardware Compatibility and Procurement

## When to use

Use this skill for:

- Determining whether RAM, SSDs, GPUs, drives, docks, or adapters can be reused
- Comparing internal installation with external-enclosure or adapter reuse
- Sourcing used/refurbished laptops, desktops, mini PCs, workstations, NAS hardware, or lab nodes
- Designing a purchase around parts the user already owns
- Assessing whether to keep, sell, or repurpose spare hardware

This is a compatibility-and-buying workflow, not a generic product roundup. The deliverable is a short, verified candidate set and a decisive recommendation.

## 1. Recover project intent before researching products

Identify the independent need and canonical roadmap first. A spare part is not by itself a reason to buy another machine.

Ask or retrieve:

- What machine or capability is actually being replaced or added?
- What workload must run now?
- What future role is plausible but not yet approved?
- Which purchases are already higher priority?
- Is portability, battery life, repairability, Linux support, CUDA, quiet operation, or low idle power decisive?

Use live project sources for active state. Use vault notes only for durable goals and boundaries.

### Rebaseline when the interface and compute roles separate

When a user's preferred daily operating environment changes, re-evaluate the architecture from the workload outward instead of preserving an expensive compute lane because its operating system or industrial design was attractive.

- Separate the **client plane** (portable human interface) from the **control**, **compute**, **data**, and **management/recovery** planes.
- Ask which capability independently justifies each specialized path. An OS preference alone does not justify a multi-node accelerator cluster.
- Mark lanes explicitly as `active`, `prepared/optional`, or `retired`; preserve useful research, but remove retired-lane purchases, reserved rack capacity, fabrics, and accessory assumptions from the active roadmap.
- Keep long-running jobs and canonical data in the backend so laptop sleep, replacement, or disconnect does not interrupt work.
- Treat rack depth, U budget, power, cooling, noise, remote recovery, and service access as compatibility gates—not furniture decisions added after compute purchases.
- Build the bare steel rack and validate representative load before adding a decorative surround or acoustic treatment.
- When the active hardware roadmap lives in Google Sheets, rebaseline the coupled rows, formulas, tags, filters, and guardrails together; a syntactically valid preserved link can still target the retired product class.

See `references/thin-client-rack-homelab-architecture.md` for the layer model, decision tests, rack-sizing workflow, and safe furniture-finish sequence. See `references/hardware-roadmap-sheet-rebaseline.md` for the formula-preserving mutation and readback procedure.

## 2. Identify every reusable component exactly

Read the label and connector. Record:

- Manufacturer and part number
- Capacity
- Generation, speed, and interface
- Physical form factor and pin/key type
- ECC/non-ECC and registered/unbuffered status
- Rank/organization and voltage where relevant
- For SSDs: NVMe versus SATA, M-key/B-key, physical length, PCIe generation and lanes

Do not claim two modules are a matched kit when only one label is visible. Preserve uncertainty explicitly.

## 3. Build hard compatibility gates

For memory, verify:

- Desktop UDIMM versus laptop SO-DIMM
- DDR generation
- Replaceable slots versus soldered memory
- Number of physical slots
- Maximum capacity per slot and total
- Supported speed and likely downclocking behavior
- ECC and rank restrictions

For storage, verify:

- NVMe/PCIe versus M.2 SATA
- Keying and physical length
- Slot generation and lane width
- Cooling/thermal-pad requirements
- Whether a sealed system supports only external reuse

Use manufacturer service manuals, setup/spec pages, PSREF, or QuickSpecs as the compatibility authority. Retail listings are discovery, not proof.

When the user explicitly requires **upgradeable system RAM**, make it a hard admission gate before ranking: remove every soldered-only candidate and rebuild the shortlist. Do not keep a fixed 32 GB machine as an “otherwise better” recommendation unless the user reverses the requirement. Prefer two physical SO-DIMM slots; disclose one-slot or soldered-plus-slot designs as materially different. An upgradeable SSD does not satisfy an upgradeable-RAM request.

Physical fit alone is insufficient. For workstation and Xeon systems, verify the exact CPU/platform accepts the user's ECC or non-ECC memory; never infer support merely because the module fits the SO-DIMM slot. Likewise, verify the exact M.2 length (2242 versus 2280), not just “NVMe.”

## 4. Research candidates by class

Create a bounded ladder rather than dumping models:

1. **Cheapest sensible fit**
2. **Best overall fit**
3. **Specialized fit** only when a real workload justifies it

When the user relaxes a component-reuse constraint, restart the comparison from the desired outcome rather than merely appending newer models to the old shortlist. For premium thin-and-light laptops, split candidates into balanced value, maximum portable performance, battery/display portability, and business/Linux/upgradeable lanes. Do not equate a newer processor with higher sustained performance: identify CPU power class, cooling limits, iGPU/dGPU role, and battery tradeoff.

For used computers, compare off-lease business systems before consumer models. They generally provide better service documentation, replaceable components, ports, and parts availability. Consumer or creator systems can still win when adequate soldered memory, a materially better display, lower weight, and buyer protection produce the better complete machine—but only when replaceable system memory is not a hard requirement.

Four memory slots in laptops usually indicate a mobile workstation. Treat the extra capacity as a tradeoff against weight, heat, noise, charger size, battery life, and price—not as an automatic upgrade.

See `references/component-first-used-computer-research.md` for the detailed sourcing, used-device trust gate, model-family patterns, and post-install verification checklist. See `references/premium-thin-light-laptop-procurement.md` when the reusable-part constraint is dropped and the search shifts to modern, light, metal, display-sensitive laptops.

## 5. Price the whole working system

Compare:

- Net resale value of the spare component
- Full acquisition cost of a compatible machine
- Charger, battery, storage, dock, adapter, shipping, and taxes
- Immediate utility of the machine
- Opportunity cost against roadmap priorities

Do not recommend spending materially more simply to avoid selling a low-value spare part. Conversely, when the user independently needs a replacement machine, reusing compatible parts can create real value.

Use current sold or active marketplace evidence and label auctions, refurbished listings, missing accessories, and parts-only units correctly. Give target and walk-away ranges, not false price precision.

## 6. Used-device trust and condition gate

Before endorsing an exact listing, verify or require:

- No BIOS or administrator password
- No MDM, Windows Autopilot, organization enrollment, or unreleased asset lock
- Absolute/Computrace state disclosed where relevant
- Battery health or a return window sufficient to test it
- Correct display resolution/panel type
- Functional charging, hinges, keyboard, trackpad, camera, and critical ports
- Correct charger included
- Exact model, CPU, and configuration
- Reputable seller and practical return policy

### Direct-listing verification gate

Search results, shopping snippets, related-item cards, and marketplace indexes are discovery only. Before sending an exact purchase link:

1. Open the exact item page and confirm the URL/item ID resolves to the stated product.
2. Confirm a live purchase control or explicit in-stock state, not merely an indexed result.
3. Reconcile the title, item specifics, seller description, and photos. Reject storage, CPU, resolution, or model contradictions rather than choosing the most favorable field.
4. Read seller notes for screen tint, dead pixels, missing battery, remote management, lock state, and other defects hidden below the title.
5. Record current item price, shipping, import fees, condition, quantity, return payer/window, and warranty.
6. Verify display quality from the exact machine type/SKU when possible. A family-level “up to 4K/400 nits” specification does not prove the listed unit has that panel; “FHD” alone does not establish brightness or color gamut.
7. Verify chassis material at the requested strictness. “Aluminum lid,” “metal cover,” carbon composite, and “premium design” do not prove an all-metal chassis; use manufacturer material claims or a credible teardown/review.
8. When exact-SKU reseller records conflict—especially on panel brightness, gamut, privacy layers, memory, or storage—preserve the conflict and require serial/product-number/panel-ID confirmation. Never choose the more favorable record silently.
9. For location- or login-gated marketplaces, treat public snippets as leads. Do not present an exact listing as verified when price, location, and active status cannot be read from the live page.
10. When the user supplies a shared Marketplace link, preserve the whole-system gates. A machine may have two SO-DIMMs yet still fail a light/metal/display requirement; an attractive discrete GPU does not erase those failures. Sparse share metadata and a family-level photo are insufficient to certify the CPU, machine type, panel, or memory layout.

Reject stale item IDs that now resolve to an unrelated product, and programmatically verify the final requested count, unique URLs, live purchase state, and budget compliance before answering. See `references/used-listing-direct-verification.md` for the compact evidence schema, sparse shared-link workflow, seller evidence request, and rejection rules.

### Deal aggregators and affiliate roundups

Treat deal indexes, dynamic configuration catalogs, and affiliate recommendation sites as candidate-discovery and price-history sources—not as compatibility authorities or final purchase surfaces.

- Recover the user’s hard gates before applying site filters.
- Inspect the complete catalog or relevant category, not only featured cards; count and deduplicate extracted records programmatically.
- Treat labels such as “Upgradeable RAM,” “Linux ready,” “metal,” and “bright display” as hypotheses. Verify exact-SKU memory layout, slot count, chassis materials, panel, and platform support independently.
- Reject sentinel prices, stale offers, unresolved redirects, and aggregator/retailer configuration conflicts.
- Record aggregator and direct retailer prices with a check time. If they disagree, use the later verified retailer price and label the aggregator record stale or unresolved.
- Rebuild the shortlist after exact-SKU verification; do not keep a failed hard-gate item because its display, GPU, or discount is attractive.

See `references/deal-aggregator-validation.md` for the catalog-to-shortlist workflow, filter and price integrity checks, configuration-conflict gate, extracted-feed sanity checks, and recommendation format.

For Linux-first systems, prefer well-supported integrated Intel or AMD graphics unless a discrete GPU serves a defined workload. Do not oversell an old low-VRAM workstation GPU as useful AI acceleration.

## 7. Present a decisive answer

Use a compact comparison table with:

- Exact model/generation and purchase link
- CPU/GPU performance lane rather than processor name alone
- Confirmed slots/interface, installed capacity, and soldered/replaceable status
- Verified weight and chassis material when portability/build are requirements
- Exact panel quality: resolution, brightness, gamut, refresh rate, and touch/privacy/OLED status
- Current delivered price, condition, returns, and warranty
- Key tradeoff
- Verdict

Then state one primary recommendation, one budget alternative, and one specialized option if justified. Distinguish **buy now** from **watch for** when a model is attractive but no safe exact listing is verified. Include the purchase trigger and walk-away condition. Avoid overwhelming the user with every technically compatible product.

## 8. Verify after acquisition or installation

During the return window:

- Update firmware from the manufacturer
- Run a full memory diagnostic such as MemTest86
- Confirm recognized capacity, speed, and channel configuration
- Inspect SSD SMART/health and sanitize reused storage
- Test battery, charging, sleep, Wi-Fi, display output, camera, keyboard, and ports

“Compatible” is not the finish line. The result must be a tested machine that serves the intended workload without derailing higher-priority spending.

## Pitfalls

- Confusing similarly named models or generations with different memory layouts
- Trusting “upgradeable” without confirming two real slots
- Assuming newer generations preserve DDR4 rather than switching to DDR5 or soldered memory
- Buying a node merely because spare RAM exists
- Treating active marketplace asking prices as completed-sale value
- Sending indexed or related-item links without opening the exact live listing
- Trusting a listing title when item specifics or seller notes contradict it
- Treating a model family’s maximum display option as the exact unit’s panel
- Calling SO-DIMM memory compatible without resolving ECC/non-ECC platform rules
- Presenting login- or location-gated marketplace snippets as verified inventory
- Ignoring charger, battery, lock state, and return-policy costs
- Recommending four-slot workstations to users who actually need a portable daily laptop
- Equating a newer, more efficient processor with higher sustained multicore performance
- Calling a laptop all-metal because only its lid or top cover is aluminum
- Treating 16 GB of soldered memory as harmless when the workload or prior request implies a 32 GB floor
- Continuing to rank soldered-memory candidates after the user explicitly makes upgradeable RAM a hard requirement
- Treating an upgradeable SSD or a soldered-plus-slot design as equivalent to two replaceable RAM slots
- Letting an attractive GPU or low price bypass the user's weight, chassis-material, display, or return-policy gates
- Promoting a low price despite seller-noted screen scratches, tint, pressure marks, dents, bad keys, blocked ports, or missing components
- Silently resolving conflicting exact-SKU specifications in favor of the better display or configuration
