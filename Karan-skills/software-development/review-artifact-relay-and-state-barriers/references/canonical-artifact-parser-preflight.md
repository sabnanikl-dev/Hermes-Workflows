# Canonical Artifact Parser Preflight and Same-Head Recovery

Use this reference when Reviewer A/B/Integration output must survive a repository-owned parser, relay, and exact-head GitHub readback.

## Semantic prose is not parser proof

A reviewer can substantively perform adversarial checks and still produce an invalid transport artifact. If the shipped parser requires canonical standalone declarations, headings or bullets that merely imply those declarations do not count.

For example, valid `ROLE`, `HEAD`, `STATUS`, and `BLOCKING` lines may still be rejected if the body lacks a parser-required declaration such as:

```text
KILL-SWITCH: <adversarial condition tested and result>
```

Never infer parser validity from human readability or substring checks.

## Exact finding-record parity

The canonical check is stronger than “both surfaces mention the same finding ID.” The lane final message and prepared artifact must carry a one-to-one set of `FINDING:` records with the same:

- ID;
- severity;
- one-line summary text.

A pass artifact and pass final message can therefore fail transport when one paraphrases the summary. Treat that as reviewer transport drift, not an implementation blocker, only after reading both retained surfaces and confirming there is no substantive disagreement.

Never patch, reconstruct, or manually restate the reviewer-owned artifact. Rerun only the affected reviewer role on the unchanged full head and unchanged frozen packet. Use a fresh detached clean worktree, preserve credential-free execution, and add an explicit focus line:

```text
Every FINDING line in the final message must be byte-for-byte identical to the corresponding FINDING line in the prepared artifact.
```

Then parse the lane verdict, validate the raw prepared body with the shipped `read_prepared`/finding-parity path, create and validate the redacted publication copy, relay through the configured trusted identity, and read the newly attributable immutable GitHub artifact back. Freeze a fresh packet only after that artifact is visible; downstream Reviewer B/Auditor packets must include the corrected upstream evidence.

## Required three-stage proof

### 1. Prepared-body parser preflight

Before external relay, run the repository's shipped parser against the exact body file under every supported runtime relevant to the PR. Verify both `ok` and the parsed claim:

- expected role;
- exact full head SHA;
- status;
- integer blocker count;
- required adversarial declarations, signature, and runtime fields.

If parser validity depends on standalone declarations, state the full schema literally in the reviewer prompt rather than naming only one example:

```text
The artifact MUST include each standalone line exactly once:
ROLE=<configured role>
RUNTIME=<pinned model/reasoning>
HEAD=<full exact SHA>
STATUS=pass|fail
BLOCKING=<plain integer>
KILL-SWITCH: <adversarial condition tested and result>
```

A vague instruction such as “include the head, blocker count, checks, and signature” can yield a substantively excellent but parser-invalid artifact. Preflight the prompt text itself before launching an expensive reviewer. Also require the exact machine footer/marker expected by the launcher and prove that marker and parsed claims agree.

### 2. Relay identity/head gate

Immediately before relay:

1. re-query PR `headRefOid`;
2. reject stale output;
3. transport through the configured reviewer identity outside the reviewer process;
4. preserve transport-only provenance;
5. never expose relay credentials to the reviewer lane.

Reviewer A may own formal review state. Reviewer B and the Integration Auditor normally use signed conversation comments when roles share one GitHub account.

### 3. GitHub readback parser preflight

After relay, fetch the exact created review/comment using the returned immutable ID. Verify:

- expected author and artifact surface;
- exact head declarations and, for formal reviews, GitHub `commit_id`;
- role/status/blocker/runtime/signature fields;
- the **actual fetched GitHub body passes the shipped parser**.

The local body is not proof of what GitHub retained.

## Same-head transport-only recovery

When the Integration Auditor finds a semantically sound but parser-invalid reviewer artifact:

1. Preserve and relay the failed audit artifact; do not erase the evidence trail.
2. Classify it as artifact transport/format—not implementation—only when the auditor confirms no code defect.
3. Do **not** launch the builder, consume a fix attempt, push a commit, or invalidate independently valid same-head upstream evidence.
4. Rerun the affected reviewer role at the unchanged exact head with explicit canonical-output requirements.
5. Parse the prepared body before relay.
6. Relay under the reviewer identity and parse the fetched GitHub body after relay.
7. Refresh the evidence packet and rerun every downstream lane whose proof depended on the invalid artifact, normally the Integration Auditor.
8. Retain earlier same-head Reviewer A evidence only when its body, GitHub readback, and exact-head binding remain independently valid.

A same-head artifact correction is not a code repair cycle. It is still a fresh ordered transport proof and must be disclosed.

## Read-only reviewer probes

Decide before launch whether mandatory tests create temporary files:

- If they do, use the workflow's supported disposable workspace-write mode where safe.
- If the lane must remain fully read-only, parent Hermes runs the deterministic probe on the exact head, freezes complete logs plus SHA-256 hashes in the packet, and the reviewer independently inspects the probe/source/tests and states the transport limitation.

A reviewer-side inability to create scratch files is infrastructure evidence, not product evidence. Never replace exact-head parent execution with invented output.
