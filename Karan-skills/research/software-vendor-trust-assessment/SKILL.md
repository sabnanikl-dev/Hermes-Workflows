---
name: software-vendor-trust-assessment
description: "Use when vetting software privacy and compliance claims."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, saas, privacy, security, compliance, trust-centers, vendor-risk]
    related_skills: [research-workflow, grounded-citations]
---

# Software Vendor Trust Assessment

## Overview

Use this class-level workflow to assess whether a SaaS product, AI app, connected device, or software vendor has supplied meaningful evidence for privacy, security, and compliance claims.

The core discipline is to separate **claims, hosted artifacts, independent issuers, observed behavior, and contractual commitments**. A polished trust center or compliance badge is an evidence-distribution surface, not proof by itself.

## When to Use

- A vendor claims SOC 2, ISO 27001/27701, HIPAA, GDPR, PCI DSS, or similar status.
- Documentation exists mainly on the vendor's own website.
- A Drata, Vanta, SafeBase, or comparable trust center gates reports behind name/email or an NDA.
- The product records audio, handles health/financial/client data, uses LLM subprocessors, or otherwise has surveillance potential.
- The user asks whether a product is trustworthy, spyware, private, secure, or safe for regulated data.
- Procurement needs a bounded `USE / DON'T USE / NEEDS MORE INFO` verdict.

## Evidence Model

Classify every important finding:

1. **Vendor claim** — marketing copy, badge, FAQ, self-attestation.
2. **Hosted artifact** — report/certificate distributed by a trust-center platform.
3. **Independent issuer** — auditor, accredited certification body, penetration-testing firm, or regulator.
4. **Observed behavior** — independently reproduced permissions, network traffic, retention/deletion behavior, or data flows.
5. **Contractual commitment** — DPA, BAA, retention term, breach notice, or subprocessor obligation covering the exact service.

Never use the trust-center host's logo as evidence that the vendor passed an audit. Never collapse these categories into one opaque trust score.

## Workflow

### 1. Freeze the exact claim

Capture the exact wording, URL, date checked, product name, and account tier. Distinguish:

- certified
- compliant
- assessed
- attested
- hosted in a certified data center
- designed to support compliance

These statements carry different evidentiary weight.

### 2. Establish legal and product scope

Verify:

- Legal entity and jurisdiction
- Exact app, device, API, account tier, and infrastructure covered
- Audit/assessment period and expiration
- Data regions and residency choices
- Subprocessors and subservice organizations
- Carve-outs, exceptions, and customer responsibilities

A parent company's certificate, cloud provider's certification, or data-center badge does not automatically cover the product being assessed.

### 3. Validate the issuer and artifact

For each artifact, capture issuer, report/certificate number, dates, scope, opinion, exceptions, and renewal status.

- **SOC 2 Type II:** inspect the actual report; check CPA firm, review period, opinion, exceptions, subservice organizations, carve-outs, and complementary user-entity controls.
- **ISO 27001/27701:** verify certificate number, legal entity, scope, dates, certification body, and accreditation chain.
- **HIPAA:** do not describe a private assessment as a government-issued certification. Identify assessor, criteria, scope, dates, qualifications, and whether the vendor will sign a BAA covering the exact service and subprocessors.
- **Penetration test:** distinguish a dated executive summary from a full report; check tester, scope, unresolved findings, and retest status.

### 4. Analyze the trust-center gate

A name/email/NDA gate is not automatically malicious. Detailed SOC 2 and penetration-test reports can expose sensitive architecture or findings. However, determine what relationship the gate creates.

Check whether the platform supports:

- Manual approval or denial
- NDA acceptance
- Watermarking
- Time-limited access
- Email/domain allowlists
- Notifications to the vendor
- CRM matching, opportunity enrichment, or sales workflows

State capability precisely: “the platform supports CRM matching” is not proof that a particular vendor enabled it.

Recommended transparency standard: publish sanitized certificate metadata publicly and reserve detailed reports for NDA-gated access.

### 5. Reconstruct actual data flow

For privacy-sensitive products, answer:

- What is processed locally versus uploaded?
- Is cloud processing mandatory?
- What changes when sync or telemetry is disabled?
- Which cloud, model, analytics, support, and advertising providers receive data?
- Is provider retention zero, limited, or unspecified?
- Can vendor personnel access content, and under what controls?
- Are identifiers used for analytics, attribution, personalization, or advertising?
- What backup, retention, account-deletion, and data-subject-request windows apply?

Read the privacy policy, trust FAQ, DPA, BAA, terms, subprocessor list, and product documentation as separate evidence sources. Reconcile contradictions explicitly.

### 6. Separate “secure” from “not spyware”

Compliance evidence may show that controls existed within a stated scope and period. It does not prove the software performs no undisclosed collection, that all behavior is inside audit scope, or that future releases remain unchanged.

For high-risk products, add independent technical observation:

- Permission inventory
- Network destination and DNS/API endpoint capture
- Behavior with optional sync/telemetry disabled
- Local-storage and backup behavior
- Account deletion and data-subject-request test
- App/device version and observation date

Do not label software “spyware” without evidence of concealed or unauthorized surveillance. Prefer precise findings such as “cloud upload is mandatory,” “marketing identifiers are shared,” or “deletion could not be independently confirmed.”

### 7. Produce a bounded verdict

Use an evidence table:

| Claim | Vendor wording | Independent issuer | Scope/dates | Exceptions | Observed behavior | Confidence |
|---|---|---|---|---|---|---|

Confidence labels:

- **Claim only**
- **Artifact located**
- **Artifact independently validated**
- **Behavior independently observed**
- **Contractually committed**

Then issue one verdict:

- **USE** — evidence and contract cover the intended risk and scope.
- **DON'T USE** — material contradiction, missing control, unacceptable collection, or contract gap.
- **NEEDS MORE INFO** — specify the exact missing artifact or answer.

For regulated or highly sensitive data, default to `NEEDS MORE INFO` until independent evidence and the relevant contract cover the exact service.

### 8. Evaluate agent-tool registries and credential brokers by operating mode

For products that combine an API marketplace, secret vault, MCP server, skill registry, proxy, or remote CLI runner, do not issue one blanket verdict. Separate the modes because each creates a different trust boundary:

1. **Vendor-funded catalog calls** — the service uses its own provider accounts; the customer supplies only a scoped service token and prepaid balance.
2. **Hosted credential vault/proxy** — the customer uploads API keys or OAuth roots that the service can decrypt at runtime.
3. **Remote CLI execution** — credentials enter a subprocess with additional filesystem, network, command-allowlist, output-redaction, and process-isolation risks.
4. **Self-hosted deployment** — removes the vendor as data processor but transfers patching, backups, key custody, availability, and network-hardening duties to the operator.

For each mode:

- Identify the uniquely valuable capability versus the user's existing agent stack. Native MCP, local skills, profile isolation, direct API clients, and local secret storage may already cover most of the registry; the catalog or metered access may be the only net-new value.
- Treat encryption at rest as protection against a database-only compromise, not as zero-knowledge, when the running server holds a decryption key. State plainly who can combine database access with runtime/environment access to recover credentials.
- Reconcile current code and live product behavior against the security policy, privacy policy, terms, pricing, and README. Material contradictions include claiming network/filesystem isolation where the security model says it is deferred, or legal pages saying “free/no payment data” after prepaid billing ships.
- Inspect installer blast radius before recommending `curl | sh`: package source, version pinning, global skill fan-out, MCP/config writes, certificate-authority creation, shell hooks, privilege escalation, and whether the target agent is actually supported. Prefer manual or isolated installation during evaluation.
- Check maturity separately from code volume: project age, pre-1.0 status, maintainer concentration, real version tags/releases, current default-branch CI, security scanning, disclosure channel, SLA/support terms, and whether docs are synchronized with shipped behavior.
- Check **self-host parity** rather than assuming the source package reproduces the hosted offer. Vendor-funded provider keys, negotiated pricing, approved OAuth applications, and marketplace entitlements often remain exclusive to the hosted deployment; self-hosting may preserve only the registry/vault while adding database, backup, patching, OAuth, and key-custody work.
- Treat a generic MCP `call`/proxy tool as an approval boundary. One schema may compress thousands of endpoints efficiently, but it can hide whether a request reads, spends, publishes, or deletes. Tool annotations are evidence about intent, not proof that the client will enforce human approval; verify client behavior and preserve external-mutation approval in the workflow.
- Count **schema compression** as a legitimate product benefit when a stable discovery/search tool fronts a large catalog. Compare that prompt/startup reduction against the lower semantic transparency of one generic executor.

Prefer a **staged least-privilege trial** over a binary adoption decision when the catalog is useful but the vault is not yet justified:

- dedicated account/org and revocable token;
- low spending/call cap and no payment method initially;
- no uploaded `.env`, production key, OAuth root, or server-side CLI run;
- ad-hoc CLI or one isolated agent profile before persistent/global MCP exposure;
- a small set of real read-only tasks with recorded quality, cost, latency, audit visibility, and revocation behavior;
- only then decide whether to keep vendor-funded catalog access, self-host the broker, or reject the product.

A useful verdict may therefore be mode-specific, for example: **USE the vendor-funded catalog in a bounded trial; DON'T USE the hosted credential vault yet; NEEDS MORE INFO for remote CLI execution.**

## Grounding and Wording

Use the `grounded-citations` skill for source-bearing claims. Prefer bounded language:

- “The trust-center provider distributes evidence but is not the auditor.”
- “The public badge is insufficient to validate the exact product scope.”
- “The request creates an additional data-processing relationship and may enter a sales workflow.”
- “No evidence reviewed proves absence of undisclosed collection.”
- “Do not process regulated data until the contract and independent evidence cover the exact service.”

## Pitfalls

- Treating badges as equivalent to reports
- Confusing a trust-center host with an independent assessor
- Calling HIPAA a government certification
- Assuming a platform capability is enabled by a specific vendor
- Interpreting every gated document as malicious lead capture
- Accepting “zero retention” without identifying provider, endpoint, contract, and scope
- Using SOC 2 as proof of product quality, privacy, or absence of surveillance
- Ignoring report dates, exceptions, carve-outs, or customer responsibilities
- Declaring “safe” when only self-published material was reviewed
- Writing a one-off vendor narrative instead of a reusable claim-to-evidence assessment

## Package References

- `references/trust-center-and-hipaa-notes.md` — Drata-style document gates, recursive trust, HIPAA wording, and evidence questions derived from a Plaud assessment.
- `references/agent-tool-registry-assessment-notes.md` — worked evidence pattern for separating a tool catalog, hosted vault, remote runner, and self-hosted mode; includes documentation-drift and staged-trial examples.

## Verification Checklist

- [ ] Exact claim, URL, date, product, and tier captured
- [ ] Legal entity and scope identified
- [ ] Independent issuer distinguished from trust-center host
- [ ] Report/certificate dates and exceptions checked
- [ ] Trust-center gate and possible requester-data workflow described carefully
- [ ] Data flow and subprocessors reconstructed
- [ ] Contract requirements identified for intended use
- [ ] Observed behavior separated from vendor claims
- [ ] For agent-tool registries, catalog, hosted vault, remote runner, and self-hosted modes were assessed separately
- [ ] Encryption-at-rest claims were not overstated as zero-knowledge when the service can decrypt at runtime
- [ ] Live behavior, source, security policy, privacy policy, terms, and pricing were checked for material drift
- [ ] Installer/configuration blast radius and target-agent support were inspected before recommending installation
- [ ] Maturity evidence includes current default-branch CI and operational/legal posture, not only test count or stars
- [ ] Verdict is bounded and lists remaining evidence gaps
- [ ] Current factual claims are cited
