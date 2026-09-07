# Thin-client cockpit and rack-compute homelabs

Use this pattern when a portable Linux/macOS/Windows machine is primarily the human interface while a home rack owns compute, storage, services, and long-running work.

## Layer model

1. **Client plane** — terminal, editor, dashboards, SSH/VPN, lightweight local work, and emergency fallback. Optimize for ergonomics, battery, repairability, OS support, and sufficient RAM; do not automatically duplicate rack compute with a mobile GPU.
2. **Control plane** — low-power always-on node for jump-host access, API routing, gateways, queues, automation, DNS/VPN, monitoring, and wake/shutdown orchestration. It must remain available while accelerators sleep.
3. **Compute plane** — rackmount GPU/CPU workers. Scale VRAM, node count, lanes, and fabric only from measured model-fit or throughput pressure.
4. **Data plane** — canonical NAS/object/filesystem storage plus snapshots and backup sources. Laptop-local and worker-local flash is scratch/cache, not authority.
5. **Management/recovery plane** — Ethernet, stable hostnames, keys, least privilege, persistent job execution, and out-of-band console access.

## Architecture decision test

For every proposed specialized lane, ask:

- Which measured workload cannot be served by the active path?
- Is the real attraction compute capability, operating-system experience, acoustics, industrial design, or curiosity?
- Does one proof node answer the question before a cluster purchase?
- Which shared infrastructure survives if the lane is retired?

If the user's daily-OS preference can be satisfied on the client plane, do not keep an expensive compute cluster active unless its accelerator, memory model, efficiency, or software ecosystem has an independent workload case.

Use explicit states:

- **Active** — current default purchasing and implementation path.
- **Prepared/optional** — research retained, no reserved budget/capacity, requires a workload trigger and new approval.
- **Retired** — no active rows, cables, trays, accessories, or rack space; historical evidence may remain in sources.

## Remote-work invariants

- Long-running jobs use `tmux`, `systemd`, containers, queues, or a scheduler and survive client disconnect.
- SSH uses keys and least-privilege accounts; avoid password/root login.
- Stable local DNS or VPN names prevent IP-address folklore.
- SSH-only operation still needs an initial local console and later PiKVM/IPMI/equivalent recovery.
- The client should not hold the only copy of credentials, jobs, or canonical data.

## Rack physical-plant gate

Calculate the rack-unit budget before buying the rack. Include networking/patching, compute chassis, NAS, UPS, control shelves, blanking/service space, and realistic growth. Select by the maximum installed depth including plugs, rails, and cable bend radius—not the nominal chassis depth.

For every rack item record:

- U height;
- installed depth;
- rails and service method;
- weight and caster/floor limits;
- intake/exhaust direction;
- noise;
- power topology;
- rear or roll-out access.

A typical first serious rack can consume roughly 19U before comfortable growth, making a deep 24U four-post rack a practical class of target; this is an example, not a universal size prescription. Recalculate from the actual bill of materials.

## Power and thermal sequence

1. Map the circuit, shared loads, receptacle/plug type, and continuous-load budget.
2. Treat wall circuit, UPS, PDU, and PSUs as one explicit system; never improvise adapters or daisy chains.
3. Define front intake, rear exhaust, room heat removal, humidity/dust/noise limits, and alert thresholds.
4. Build the bare steel rack.
5. Run representative compute/storage load, graceful-shutdown, service-access, and recovery tests.
6. Add furniture finish only after those tests pass.

A furniture-grade wood surround should be removable and non-structural. The steel rack carries equipment. Avoid sealed boxes, blocked exhaust, load-bearing decorative shelves, and ordinary acoustic foam inside an unvalidated enclosure.

## Procurement consequences

- Prefer rack-compatible NAS/UPS/switch/control hardware or explicitly reserve vented shelf space.
- Buy a temporary 2.5GbE switch only when it retains a durable edge/management role; otherwise compare the cost of moving directly to the intended rack fabric.
- Keep fast intra-rack networking inside the rack unless the client has a measured need for the same speed.
- Preserve standard removable storage media and protocol-level access so client devices and compute nodes can change independently.
