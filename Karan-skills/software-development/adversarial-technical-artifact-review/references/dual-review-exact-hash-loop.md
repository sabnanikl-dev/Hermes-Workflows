# Dual-review exact-hash loop

Use these contracts with two independent read-only reviewer lanes such as Claude Code and Codex. Adapt the attack surface to the artifact, but keep the output marker stable.

## Round 1 prompt contract

```text
You are an adversarial technical reviewer. Perform a READ-ONLY hostile review of:
<ABSOLUTE_PATH>

Expected SHA-256: <HASH>

First verify the exact file and hash. Do not edit any file.

Attack the recommendation as if implementation begins tomorrow. Look for:
- unsupported or stale vendor/API/licensing claims;
- hidden account, permission, authentication, quota, or platform prerequisites;
- an approval or system-of-record model that can be bypassed;
- scheduled/delivered states confused with verified external completion;
- unmodeled native/manual work, staffing, weekends, and escalation;
- retry, duplicate, timeout, cancellation, drift, and recovery gaps;
- credential, public-media, privacy, prompt-injection, or tenant-isolation risks;
- a prototype that does not test the load-bearing product claim;
- missing measurable go/no-go criteria.

Each P0/P1 finding must include:
1. artifact line(s);
2. failure/consequence;
3. minimum correction;
4. primary evidence/source when factual.

Output exactly:
# <Reviewer> Adversarial Review — Round 1
## Verdict
## P0/P1 Blocking Findings
## P2 Non-Blocking Findings
## Claim Verification Requests
## What Is Sound
## Minimum Revision Plan
DONE: STATUS=pass|fail P0=<n> P1=<n> P2=<n>

PASS only when P0=0 and P1=0.
```

## Re-review contract

```text
Review this exact revised artifact in READ-ONLY mode:
<ABSOLUTE_PATH>
Expected SHA-256: <NEW_HASH>

Prior blockers:
<ROOT-CAUSE SUMMARY>

Re-read the entire artifact. Prove or disprove closure of the prior blockers and identify regressions or new P0/P1 findings. Verify material current claims against primary documentation where possible. Do not demand implementation detail beyond what this class of artifact reasonably requires; optional hardening is P2.

Use the same severity sections and final marker.
```

## Final regression contract after P2 edits

```text
Review this final exact artifact in READ-ONLY mode:
<ABSOLUTE_PATH>
Expected SHA-256: <FINAL_HASH>

The previous round passed P0=0/P1=0. Since then only these non-blocking edits were made:
<BOUNDED CHANGE LIST>

Verify the hash, read the whole artifact, confirm those edits are accurate and non-regressive, and confirm all prior blockers remain closed.

Output:
# <Reviewer> Adversarial Review — Final
## Verdict
## P0/P1 Blocking Findings
## P2 Non-Blocking Findings
## Regression Check
DONE: STATUS=pass|fail P0=<n> P1=<n> P2=<n>
```

## Hermes reconciliation checklist

- [ ] Reviewer lanes used the same path, hash, scope, severity, and output contract.
- [ ] Reviewers were read-only and did not race on the artifact.
- [ ] Each output file was read; zero exit was not treated as PASS.
- [ ] Every P0/P1 was merged by root cause.
- [ ] Material factual claims were independently checked against current first-party docs.
- [ ] Unknown live-account facts became explicit gates rather than assumptions.
- [ ] The revision changed architecture/operating controls where needed, not only wording.
- [ ] Every post-pass edit triggered a new hash and regression review.
- [ ] Final local hash equals the hash each passing reviewer checked.
- [ ] Final summary reports residual P2 honestly without calling them blockers.

## Useful reviewer-lane execution rules

- Capture reviewer output to separate files; keep event/stderr logs separate from the final review artifact.
- For non-interactive Claude Code review lanes, prefer feeding the prompt through stdin (`claude ... < prompt.md > review.md`) over shell command substitution inside a background launcher. Command-substitution launches can exit with an empty artifact and no useful stderr even when a direct auth smoke test succeeds. After exit, require a non-empty result file and validate its final marker; an empty file never counts as a review.
- If an explicitly requested reviewer is temporarily unauthenticated, continue independent research or the other lane, restore that lane, and run it against the unchanged hash. Never claim a substitute was that reviewer.
- Prefer fresh/ephemeral sessions for each round so prior prose does not anchor the reviewer.
- For document review, read-only sandboxing is enough; reviewers need no write or deployment authority.
- Keep the final exact reviewed artifact unchanged. If a cosmetic typo must be fixed, rerun the final regression gate rather than citing a stale pass.
