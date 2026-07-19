# External Library Adoption + Pilot Issue Pattern

Use this when a repository wants to evaluate a substantial third-party library without prematurely making it part of the production architecture.

## Why split the work

Create two issues when setup risk and product-value risk can be reviewed independently:

1. **Isolated adoption/toolchain issue** — proves the dependency can be installed, pinned, smoke-tested, and kept within the repository's existing runtime/dependency boundaries.
2. **Bounded pilot/dogfood issue** — proves the library creates enough value on representative data to justify productionization.

Do not combine these into one broad “install and integrate” ticket. Installation success does not prove usefulness, and a pilot should not quietly turn into production infrastructure.

## Issue 1: isolated adoption/toolchain

Ground against the repository's current dependency contract first. If core validation/build tooling is intentionally dependency-free or lightweight, preserve that property.

Include:

- exact direct dependency pin or a documented lock strategy;
- an isolated environment or optional dependency lane rather than global installation;
- an **offline smoke check** that verifies import, installed version, and required public entry points without credentials, network calls, or model/API inference;
- explicit credential, billing, privacy, and input-handling boundaries;
- a regression criterion proving the repository's existing core commands still work when the optional dependency is absent;
- path-scoped/separate CI if optional-lane CI is justified, rather than burdening the canonical gate;
- upstream repository, license, supported runtime, evaluated release, and support-status notes.

Out of scope should explicitly exclude the pilot, production integration, account/key creation, global/profile installation, and canonical data mutation.

## Issue 2: bounded pilot/dogfood run

Make the installation issue a hard prerequisite. The pilot should answer **continue, narrow, or stop**.

Include:

- two materially different representative fixtures or workstreams when the goal is reusable adoption;
- sanitized committed fixtures plus an explicitly local-only path for larger/private evaluation inputs;
- a manually reviewed expected/gold set so misses and false positives can be measured;
- narrow task passes instead of one oversized prompt/schema;
- a candidate/staging output contract separate from canonical source-of-truth data;
- fail-closed behavior for ungrounded, malformed, unsafe, or authority-expanding output;
- deterministic no-network tests using recorded/mock output so normal CI does not require paid inference;
- generated review artifacts under an ignored build directory; commit only code, sanitized fixtures, and a sanitized report;
- recorded provider/model/version/settings and honest unknowns where usage/cost telemetry is unavailable;
- a final report comparing quality, reviewer effort, cost visibility, and privacy risk;
- a separate productionization issue only if the decision is continue or narrow.

## Source-of-truth safety

For extraction/AI libraries, “source-grounded” is not the same as “verified.” A source span can show where text came from but does not prove that the model's classification or inferred attributes are correct.

Pilot issues should therefore require:

- exact source intervals for accepted candidates;
- ungrounded output to fail closed;
- no automatic promotion to canonical statuses such as verified/approved/active;
- no direct writes into canonical files or production stores;
- human or independent-agent review before any mapping step;
- explicit handling for filesystem paths, untrusted URLs, secrets, PII, and cloud-model data transfer.

## Duplicate and boundary checks

Search adjacent issues before creation and explain boundaries. Common neighbors include:

- evidence/citation health after authoring;
- retrieval, embeddings, or semantic search;
- client/project scaffolding;
- ingestion/OCR/document parsing;
- production hosting or workflow automation.

Link them, but do not let the pilot absorb them.

## Verification after creation

Create the adoption issue first so the pilot can reference its real issue number. Re-read both live issues and verify:

- title, body, labels, state, and URL;
- the pilot names the adoption issue as a prerequisite;
- no-canonical-write and no-authority-expansion clauses survived rendering;
- existing/adjacent issues were checked and are not duplicated.
