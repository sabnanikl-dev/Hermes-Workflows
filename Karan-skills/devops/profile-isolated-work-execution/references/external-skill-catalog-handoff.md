# External Skill Catalog Handoff

Use this when Default Hermes may source task-helpful skills from a third-party catalog for a least-privilege worker.

## Catalog versus package

First determine whether the repository contains actual skill packages or only links. A clone with no `SKILL.md` files is an index, not an installable skill root. Keep it as a read-only discovery catalog and resolve each candidate to its real upstream package.

## Authorized VoltAgent catalog source

Karan explicitly authorized `https://github.com/VoltAgent/awesome-agent-skills` as a discovery source for helpful worker skills.

- Canonical local clone: `/Users/creator/projects/awesome-agent-skills`
- Verified remote: `https://github.com/VoltAgent/awesome-agent-skills.git`
- Verified baseline commit: `c97eda5e3406670f3285c6bf9eb7639a7ecc03cc` (`main`, matched `origin/main` when audited)
- License: MIT
- Repository shape at audit: catalog README with linked upstream packages; no vendored `SKILL.md` files
- Read-only compatibility smoke test: `hermes skills inspect https://officialskills.sh/anthropics/skills/skill-creator` resolved the community package and previewed its `SKILL.md` without installation

Before using the catalog later, fetch/read the current remote head and disclose drift from the verified baseline. Search the README for a task-specific candidate, then audit the linked upstream package; do not treat the catalog commit as the candidate package's provenance or bytes.

## Per-skill audit

For each candidate, record:

- catalog entry and upstream URL/identifier;
- upstream owner and repository;
- trust classification and license;
- exact frontmatter name and description;
- bundled scripts, binaries, network calls, credential names, and writable paths;
- requested tools and external mutation classes;
- whether an existing local skill already covers the need;
- approval status for sensitive or authority-expanding behavior.

Use `hermes skills inspect <URL-or-ID>` as the first read-only check. Inspection success is not installation approval.

## Safe handoff

1. Prefer an existing governed local skill when equivalent.
2. Install only the exact audited candidate; never import a whole catalog “just in case.”
3. Verify the installed skill's frontmatter name and files match the audited candidate.
4. Ensure launcher resolution is unambiguous; name collisions fail closed.
5. Add the exact skill name to a short-lived root/issue/revision/run-bound grant.
6. Pass no credentials unless the packet names the exact approved action and environment-variable names.
7. During the granted run, verify the skill is available and the task-skill residue manifest is private and correctly bound.
8. After exit, verify consumed grant and copied skill are absent.
9. Launch a fresh ungranted probe and verify the temporary skill cannot be loaded.

## Authority boundary

General permission to use a catalog as a source does not pre-approve:

- credential or account access;
- public/client-facing publication or sends;
- deploys, merges, payments, purchases, or destructive operations;
- permanent worker-profile expansion;
- profile allowlist/toolset changes;
- hub-wide or bulk third-party installation.

Those remain separately gated by the task packet and Karan's approval where required.
