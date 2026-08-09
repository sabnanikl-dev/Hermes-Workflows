# Adapter-native review packets and live transport smoke

Use this when a repository ships its own reviewer adapter or packet protocol.

## Packet rule

A review packet is an executable protocol boundary, not merely a useful JSON document. If the repository owns `packet_binding()`, `build_packet()`, `write_packet()`, `read_packet()`, sequence fields, frozen-role fields, or shell-side binding checks, generate and validate the packet through those seams.

A hand-built packet may contain every useful PR surface and still be rejected because its binding is an object instead of the canonical string, it omits required surface names, or it is frozen for the wrong lane sequence. Do not patch around this after a costly reviewer launch. Run the adapter's cheap preflight/binding checks first.

## Exact shipped-adapter smoke

A direct CLI smoke proves only the CLI. When the PR changes an adapter, also exercise the shipped adapter itself with:

1. an exact-head disposable worktree;
2. credential variables unset and an empty reviewer GitHub config directory;
3. the repository-native immutable packet;
4. a scratch artifact directory outside the worktree;
5. the exact runtime/model/reasoning/sandbox arguments the adapter will ship;
6. separate capture of narration/diagnostics, final-message stdout, and prepared artifact;
7. parser validation of the final message;
8. prepared-artifact validation against the parsed findings;
9. a clean-worktree check afterwards.

The smoke must prove both channels:

- the reviewer process itself creates the external artifact before exit;
- only the isolated final-message bytes reach verdict stdout.

A cooperative stub that writes only the final message, followed by a test that fabricates the artifact after the adapter exits, does not prove the transport contract.

## Sequenced reviewer packets

When the repository contract defines Reviewer A → Reviewer B → Integration Auditor, packets are per-lane snapshots:

- relay and read back A before freezing B's packet;
- relay and read back B before freezing the Auditor packet;
- increment the canonical sequence and bind the frozen role each time;
- re-query the live head before every relay.

Do not parallelize lanes merely because their code inspection could be independent; review-state evidence is part of the ordered contract.
