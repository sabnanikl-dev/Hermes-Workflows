# Dual-north-star hardware roadmap sheets

Use this pattern when a phased hardware shopping sheet must preserve two plausible end-state architectures—for example, a CUDA GPU-server path and an Apple-silicon distributed-compute path—without stranding early storage/network purchases.

## Core model

Split the roadmap into three layers:

1. **Shared spine before divergence** — storage, backup, management, API routing, telemetry, cabling, and general infrastructure usable by either path.
2. **North Star A** — architecture-specific compute, memory, power, chassis, and fabric.
3. **North Star B** — its own compute, memory, power, chassis, and fabric.

Create a dedicated **North Stars** tab rather than hiding the fork in row notes. Suggested columns:

```text
Layer | Shared spine before divergence | North Star A | North Star B | Purchase / architecture rule
```

Cover at least: goal, compute nodes, memory semantics, compute interconnect, storage/control network, canonical shared storage, node-local cache, backup media, divergence trigger, topology, and maturity/risk.

## Keep compute and storage fabrics separate

A fast collective/inter-node fabric is not automatically the storage network.

- Describe the compute fabric by topology, endpoint eligibility, cable count, and runtime/backend requirements.
- Keep NAS, management, SSH, monitoring, and ordinary service traffic on a conventional Ethernet control/storage plane unless primary documentation explicitly supports something else.
- Do not market distributed model sharding as a literal single shared-memory machine. State aggregate installed memory and the runtime assumptions separately.

For an `n`-node direct full mesh, verify the cable/link count with:

```text
links = n × (n - 1) / 2
```

A four-node full mesh therefore requires six direct links and three active links per node.

## Storage portability hierarchy

Prefer purchases that remain reusable even if the compute path changes:

| Tier | Portable default | Placement rule |
|---|---|---|
| Bulk capacity | Standard CMR SATA HDD | Canonical shared NAS/server pool; avoid SMR for ZFS-class use |
| Shared warm flash | Standard removable 2.5-inch SATA TLC SSD | NAS/server bays; export by NFS/SMB |
| Shared hot flash | Server-hosted U.2/U.3 or other standard enterprise NVMe | Buy only with lanes, backplane/adapter, cooling, and a defined role |
| Node-local scratch | Standard removable M.2 2280 TLC NVMe | Internal on servers or in standards-based external enclosures; never canonical data |
| Backup | Separate offline/offsite target | RAID/ZFS is not backup |

Avoid making a proprietary, host-shaped, or enclosure-locked DAS the canonical model/dataset store. The enclosure can be path-specific when the underlying drive remains removable and the data is only scratch/cache.

Use protocol-level portability for canonical data:

- NFS as the default ML dataset/model path when appropriate.
- SMB for interactive Mac/Windows access when useful.
- Separate datasets for models, datasets, checkpoints, artifacts, and backups.
- Stage active files to node-local SSD only when measured cold-start time warrants it.

## Buying and validation sequence

For expensive or maturing cluster paths:

1. Buy one proof node and validate the actual workloads.
2. Validate a two-node distributed/interconnect path.
3. Confirm topology, software versions, failure recovery, and storage staging.
4. Only then buy nodes 3–4 or the full cluster.

Do not buy the entire cluster from theoretical aggregate memory or headline link bandwidth alone. Record payload-vs-marketing bandwidth caveats, software maturity, model/runtime support, and headroom for OS/runtime/KV cache/activations.

## Evidence hierarchy

- **Primary:** platform vendor technical notes/specifications, framework distributed docs, storage vendor filesystem/hardware guidance.
- **Secondary:** independent field tests and issue trackers, clearly labeled experimental/community evidence.
- Keep headline port rates separate from normal bidirectional data mode and measured application throughput.
- If vendor setup instructions conflict across versions, anchor the sheet to an explicit OS/framework version and record the discrepancy.

## Safe sheet mutation and verification

Identify rows by stable **Item** keys, not row numbers. When inserting/removing rows:

- Rewrite dependent compatibility/audit columns in the same operation.
- Rebuild annotations by stable key; do not preserve their prior row order.
- Reset filters to the final row count and full table width.
- Read back formulas and formatted values.
- Assert required rows exist exactly once.
- Assert several known item → annotation pairs still align.
- Verify sources, permissions, and a local pre-mutation backup.

A polished new architecture tab does not compensate for shifted compatibility notes; fix alignment before reporting completion.
