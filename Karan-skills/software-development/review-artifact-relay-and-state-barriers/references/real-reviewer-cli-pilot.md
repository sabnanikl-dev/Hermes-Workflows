# Real reviewer-CLI transport and semantic-evidence lessons

Use this reference when an artifact relay moves from stubbed reviewer tests to a real Codex/Claude CLI, or when a reviewer lane returns `malformed-verdict` despite producing substantive findings.

## Normalize diagnostics away from the verdict

Real reviewer CLIs may emit prompt text, tool activity, diagnostics, and the final answer into combined process output. Prompt examples can therefore look like real terminal markers.

Adapter contract:

1. Use the CLI's supported final-message output channel (for Codex, `--output-last-message <path>` when available).
2. Keep progress/diagnostics in a separate log or stderr stream.
3. Parse only the final-message channel for terminal markers and verdict metadata.
4. Preserve watchdog reporting while the parseable channel is quiet.
5. Test a fixture where diagnostics contain marker examples and the final message contains exactly one real marker.

Do not weaken duplicate-marker fail-closed checks. Normalize the adapter boundary instead.

## Align scratch writes with reviewer isolation

A reviewer may need to write one artifact into prover-owned scratch while remaining unable to publish to GitHub or alter the exact-head worktree.

- Grant only the intended scratch write.
- Keep GitHub credentials out of the reviewer lane; use the trusted relay.
- Preserve worktree contamination checks.
- Test the real adapter shape, not only a stub that creates the artifact automatically.
- If the sandbox cannot write the requested artifact, fix the adapter/scratch contract; pasted chat output is not a substitute.

### Distinguish the two write paths

The CLI-managed final-message file and the model-written review artifact are separate boundaries. A live CLI can successfully create `--output-last-message` outside the model sandbox while the model remains unable to write the prompted artifact under `/tmp` or another prover-owned directory. Prove both paths through the shipped adapter:

1. the CLI writes one isolated, non-empty final message;
2. the reviewer process can create the exact run-scoped artifact path;
3. the exact-head worktree stays clean;
4. no publication credential reaches the lane.

A cooperative stub that writes any requested path cannot prove this boundary.

### Preserve the complete launcher contract

A final-message transport patch must not accidentally drop the rest of the real reviewer invocation. Before review, compare the adapter's actual argv/environment with the prior approved launcher and the current installed CLI help. Verify all contract-required behavior, including:

- noninteractive execution and fresh/ephemeral context;
- pinned model/provider and reasoning effort;
- user-config/rules isolation when deterministic prompts are promised;
- intended sandbox mode plus explicit writable artifact directory;
- credential-free GitHub environment;
- original process exit-status propagation.

Run one bounded live smoke with the installed CLI version and exact claimed settings, capture narration separately, and verify the final-message bytes. Unit tests prove deterministic edge cases; the live smoke proves the current CLI contract. Do not accept green parser tests as evidence that omitted launcher flags or artifact-directory access still work.

## Make prompt and parser share one grammar

The prompt must name every machine-readable record the parser counts. If the parser expects `FINDING: BLOCKING ...`, the prompt must require that exact prefix and field order. “State every blocking finding” is not sufficient.

Regression coverage:

- `BLOCKING=N` equals parsed blocking records;
- a multi-finding fixture parses to the exact declared count;
- duplicate/conflicting role, runtime, head, status, or blocking fields fail closed;
- malformed finding lines produce actionable remediation;
- the unique final `DONE:` marker agrees with the artifact;
- prompt examples and diagnostic echoes never count.

## Honor malformed-verdict budgets

1. Preserve the first failed run and retained evidence.
2. Make at most one bounded adapter/config correction when the failure contract permits it.
3. Rerun from a fresh worktree root so retained evidence stays intact.
4. After a second rejected verdict, stop and escalate rather than adding more wrappers.
5. Verify that builder, push, publication, merge, and live mutations did not occur.

A terminal `needs-Karan` can satisfy a pilot that explicitly accepts stop-and-ask with exact evidence. It is not proof that the target PR is merge-ready.

## Semantic visual evidence

Screenshot/PDF existence does not prove content. A live pilot produced PDFs with collapsed-section headings but omitted bodies while the generation gate passed.

Combine:

- required responsive captures;
- dimensions and non-empty media checks;
- PDF page/size checks;
- PDF text extraction for required body markers, not headings alone;
- mobile table-label checks when headers are hidden;
- objective contrast checks for small required text;
- human inspection for hierarchy, overflow, truncation, and protective-stop clarity.

Bind manifests to exact head, worktree, timestamp, dimensions/page size, and checksums.

## Closeout

When transport fails closed:

- quarantine substantive but invalidly transported reviewer output;
- route exact execution inventory to the owning tracker;
- collect human calibration for at least five findings (confirm/adjust/reject plus severity);
- create an additive post-pilot hardening issue rather than editing completed release evidence;
- reconcile the open parent sequence and acceptance checklist in the same tracker change;
- keep the target work item open when underlying PR work remains unresolved.

The PAPI-96 pilot is the representative case: combined output first produced duplicate marker examples; the corrected final-message path then exposed a prompt/parser finding-prefix mismatch. All configured gates were green, but reviewer publication and builder execution were correctly withheld.