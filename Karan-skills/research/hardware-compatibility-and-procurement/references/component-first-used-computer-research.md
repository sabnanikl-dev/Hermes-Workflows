# Component-First Used Computer Research

Use this reference when the user owns reusable computer components and is considering a used/refurbished system around them.

## Decision rule

Do not recommend buying a machine merely to consume a low-value spare component. Determine whether the user independently needs the machine, whether it serves an immediate workload, and whether it advances the active roadmap. Compare net resale value with total system cost and opportunity cost.

A real replacement need can make component reuse rational; an unused spare by itself usually does not.

## Compatibility evidence hierarchy

1. Manufacturer service manual or setup/specification page
2. Lenovo PSREF, HP QuickSpecs, or equivalent configuration database
3. Manufacturer parts/upgrade documentation
4. Reputable upgrade-vendor compatibility database
5. Retail and marketplace listings only for discovery and pricing

Use official documentation to prove slot count, memory type, capacity, interface, and physical fit. Do not treat a retailer’s word “upgradeable” as proof of two physical slots.

## Memory-specific checks

Record:

- SO-DIMM versus UDIMM
- DDR generation and rated speed
- ECC/non-ECC and registered/unbuffered status
- Capacity, rank, voltage, and exact part number
- Two real slots versus soldered memory plus one slot
- Maximum per-slot and total capacity
- Supported channel configurations

If only one module’s label is visible, do not call the pair matched. Verify the other label or system data and run a full memory test after installation.

## Storage-specific checks

Record:

- NVMe/PCIe versus M.2 SATA
- M-key/B-key connector
- Physical length such as 2230 or 2280
- PCIe generation and lane width
- Thermal requirements
- Internal versus external-enclosure compatibility

For reused drives, inspect SMART/health and sanitize the drive before trusting it with new workloads.

## Candidate-class patterns

### Two-slot business laptops

Selected generations of these families commonly provide two accessible DDR4 SO-DIMM slots, but exact generations must be verified:

- Dell Latitude 5420/5430
- Lenovo ThinkPad L-series
- HP EliteBook 845 and ProBook 445
- Intel Framework Laptop 13 generations that use DDR4

These are usually the best balance for a daily replacement laptop: lower weight, USB-C charging, good service documentation, and affordable off-lease supply.

Beware similarly named models. ThinkPad T-series and slim workstation variants often use soldered memory plus one slot. Newer generations may switch to DDR5 or fully soldered memory.

### Four-slot mobile workstations

Four-slot laptops exist primarily in mobile-workstation families:

- Dell Precision 7x50/7x60
- Lenovo ThinkPad P15/P17
- HP ZBook Fury

They can support 64–128GB, but are commonly heavier, hotter, noisier, more expensive, and paired with large chargers. Recommend one only when the user needs workstation CPU performance, several drives, large memory capacity, or a specific discrete GPU. Do not buy one merely to leave two extra memory slots empty.

An older 4GB workstation GPU is not meaningful local-LLM capacity. For Linux-first use without a defined CUDA workload, integrated Intel or AMD graphics often produces a better daily machine.

## Whole-system price model

Include:

- Machine price and shipping
- Charger if missing
- Battery replacement allowance
- Storage if absent
- Dock or adapter only if genuinely required
- Marketplace fees or taxes where relevant
- Value of included RAM/storage that may be retained or resold

Prefer low-memory configurations when the user already owns RAM, but do not reject a better complete-system deal simply because it includes memory. Treat active asking prices as ranges, not completed-sale value.

## Used-device trust gate

Before endorsing an exact listing, verify or require:

- No BIOS/administrator password
- No active MDM, Windows Autopilot, organization enrollment, or unreleased asset lock
- Absolute/Computrace state disclosed where relevant
- Battery health or a sufficient return window
- Correct screen resolution, panel type, and brightness class
- Working USB-C charging, hinges, keyboard, trackpad, camera, and critical ports
- Correct charger included
- Exact model, processor, and configuration
- Seller history and practical return policy

Avoid accidental low-resolution panels and privacy-screen variants unless specifically wanted.

## Recommendation format

Return a compact ladder:

1. **Best overall:** the system that best balances useful life, price, and the user’s real workload.
2. **Budget:** the cheapest machine that remains supportable and pleasant enough to use.
3. **Specialized:** a workstation or repairability-first option only when its tradeoffs are justified.

For each, include exact generation, target CPU, verified slot/interface facts, current observed price range, purchase trigger, and walk-away condition. Name one primary recommendation rather than leaving the user with an unranked list.

## Post-install proof

During the return window:

- Update manufacturer firmware
- Run MemTest86 or equivalent full memory diagnostic
- Confirm capacity, speed, and channel mode
- Check storage SMART/health
- Test charging, battery, sleep, Wi-Fi, display output, camera, keyboard, and ports

A successful result is a tested machine that serves the intended workload—not merely a part that physically fits.
