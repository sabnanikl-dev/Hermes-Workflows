# Three-skill agent factory comparison notes

## External pattern reviewed

A public workflow presented a three-skill factory:

- **spec:** codebase research plus iterative user interview; stable acceptance criteria and non-goals; human applies the readiness label;
- **build:** repair requested changes first, otherwise claim one approved unassigned issue, implement only its contract, verify, and open one PR;
- **review:** inspect one PR at an exact head, check required CI and mergeability, post a structured verdict, and set queue labels;
- **human boundary:** humans approve specs and merge.

The associated video also described repeated five-minute loops, browser testing, messaging notifications, and reaction-triggered merge. Repository inspection showed the shipped public artifact was primarily three Markdown skills, a static validator, and CI. Persistent workers, messaging, webhooks, browser evidence, durable leases, recovery, and reaction merge were roadmap patterns rather than implemented runtime components.

## Useful mechanics to borrow

- explicit human-only `agent-ready` gate;
- stable `AC-N` / `NG-N` issue contracts;
- one agent-day-or-less issue sizing;
- one issue per PR;
- repair queue before new work;
- blocked issues leave the automated queue;
- exact-head review comments and labels;
- no required CI means human escalation, not an automatic green result;
- humans retain merge authority.

## Mechanics not to copy blindly

- repeated LLM polling every five minutes;
- Linear assignment as the only lock when sessions share one identity;
- single same-context/same-identity review when a stronger independent reviewer stack already exists;
- marketing claims such as percentage automation or productivity multipliers without measurements;
- emoji-triggered merge without user identity, event dedupe, exact approved SHA, and live re-verification;
- treating a static phrase validator as end-to-end workflow proof.

## Adaptation into the stronger Hermes stack

Preserve:

- Claude builder authority;
- Reviewer A/B plus isolated Integration Auditor;
- PR as artifact bus;
- exact-head verification;
- bounded fix cycles;
- Karan merge approval;
- default Hermes final integration and verified closeout.

Add around it:

- a lean PM-spec contract skill;
- an explicit Linear approval predicate distinct from generic Ready;
- a one-pass queue runner;
- a local expiring lease/run ledger;
- read-only status inspection;
- recovery supervision;
- quiet deterministic watchdogs;
- signed webhook wakeups after manual pilots;
- Telegram/dashboard merge-ready packets.

## Session-derived local audit signals

When auditing a similar system, check for discrepancies such as:

- a profile declaring a small role-native set while its on-disk skills still expose the bundled library;
- generic Ready work containing human, credential, access, or client-input tasks;
- In Progress work with no assignee;
- a large root workflow skill whose rare edge cases belong in references;
- many paused/stale crons but no factory watchdog;
- webhook platform disabled while plans assume event triggers;
- plaintext messaging credentials duplicated into specialist profile configs.

These are evidence to harden before persistent autonomous workers, not reasons to discard the existing architecture.

## Recommended initial automation footprint

Start with at most:

1. one deterministic factory watchdog, silent unless a condition opens or resolves;
2. one read-only weekday director/control-plane brief;
3. temporary finite `no_agent` per-run status jobs for long work.

Keep new-work execution manual until several low-risk repo-only pilots demonstrate no duplicate claims, stale-head approvals, unrelated changes, or alert spam.
