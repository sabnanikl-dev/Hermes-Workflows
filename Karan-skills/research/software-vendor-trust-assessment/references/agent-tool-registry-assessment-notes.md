# Agent-tool registry assessment notes

Worked example captured from an assessment of `superdesigndev/treg` on 2026-08-11 at commit `2b7925c4b7fd012da6d0bf4c262723c05a92a87c`. This is an evidence-pattern reference, not a standing verdict. Re-check the live service, current default branch, legal pages, and CI before reusing any product-specific conclusion.

## Why mode separation mattered

The product combined four materially different offers:

1. A vendor-funded, metered catalog of API endpoints.
2. A hosted vault/proxy for customer API keys and OAuth tokens.
3. Local and server-side CLI execution with injected credentials.
4. A self-hosted registry.

The useful conclusion was not “safe” or “unsafe.” The catalog could merit a low-risk trial while the hosted vault and remote-runner modes remained unjustified for production credentials.

## Evidence patterns worth repeating

### Net-new value versus stack overlap

The catalog supplied access to many occasional-use data providers without separate subscriptions. The key/skill/MCP registry overlapped with an agent stack that already had native MCP, local skills, direct API integrations, isolated profiles, and local credential handling. The adoption question therefore narrowed to: **Is metered catalog access valuable enough to add another trust boundary?**

### Encryption-at-rest wording

The source used Fernet encryption with one server-held environment key and decrypted credentials at call time. Correct interpretation:

- useful against a database-only disclosure;
- not zero-knowledge;
- not protection against compromise or control of both runtime environment and database;
- hosted operator remains a high-trust credential broker.

Source examples:

- `src/treg/crypto.py`
- `src/treg/proxy.py`
- `SECURITY.md`

### Documentation drift as a material finding

Three contradictions changed the risk verdict:

- `SECURITY.md` said server-side runs did not yet have filesystem/network isolation, while `src/treg/web/privacy.html` claimed server-side runs had both.
- The README/live product described prepaid metered calls and top-ups, while the July 2026 terms/privacy text still described the hosted service as free and said it took no payment data.
- The privacy policy said there were no analytics scripts or session replay, while the live `/meta` response advertised a PostHog project and `src/treg/web/index.html` initialized PostHog, enabled session recording, and identified signed-in users by email and team. A public analytics project key is not itself a leaked secret; the finding is the policy/behavior mismatch.

This is stronger evidence than a generic “docs may be stale” warning. Compare the exact shipped behavior and source-backed security model with the current contractual/privacy representation.

### Generic MCP executors and approval semantics

The MCP front door exposed a small, stable discovery surface rather than one schema per catalog endpoint. That is real value for prompt size and startup cost. The tradeoff was a generic `call` tool that could relay GET, POST, or DELETE operations and spend money without modeling upstream semantics.

Assessment rules:

- inspect the MCP tool annotations, but do not assume the client enforces them;
- test whether the client actually prompts for open-world/destructive calls;
- preserve the user's external-mutation approval rule in the agent workflow even when the server marks the tool destructive;
- prefer read-only endpoint IDs during the first trial and keep the MCP out of default/messaging profiles until behavior is proven.

### Self-host parity

The open-source server did not automatically reproduce the hosted product's access advantage. The hosted deployment's provider subscriptions, approved OAuth applications, pricing arrangements, and platform credentials were separate operational assets. A self-hoster would generally need to supply replacements while also operating the database, Fernet key, backups, OAuth callbacks, upgrades, and network controls.

Always ask: **Which capabilities come from the code, and which come from the vendor's accounts or approvals?** Do not recommend self-hosting as a way to retain catalog value unless that parity is demonstrated.

### Installer blast radius

The convenience installer did more than install a CLI: it installed a package extra, pointed the CLI at a hosted server, bootstrapped skills into detected agents, and could register MCP when given a token. Hermes support was manual rather than safely auto-written. Evaluation guidance:

- inspect the installer before running it;
- prefer an isolated/pinned package install or manual MCP entry;
- avoid global multi-agent fan-out during a trial;
- verify whether any local proxy mode creates a certificate authority or changes firewall/sandbox configuration.

Relevant files:

- `src/treg/web/install.sh`
- `src/treg/mcp_install.py`
- `src/treg/agents.py`
- `src/treg/localproxy.py`
- `src/treg/egress.py`

### Maturity evidence

At review time the repository was new, pre-1.0 (`0.8.0`), concentrated among two human contributors, and explicitly early access/no SLA. Security policy, CodeQL, gitleaks, and a large test suite were positive signals. Current default-branch CI had one stale landing-copy assertion failure after 1,307 tests passed. Correct reading: serious engineering effort, but not yet a stable credential authority.

Do not treat test count as a substitute for operational history, independent assessment, green default-branch CI, or synchronized legal/security documentation.

## Bounded trial template

Use this when catalog value is plausible but hosted credential trust is not:

- Create a dedicated org/account and revocable agent token.
- Use only vendor-funded catalog calls and promotional credit.
- Set a low call/spend cap; add no payment method initially.
- Upload no `.env`, production key, OAuth root, client credential, or private skill.
- Disable/avoid remote CLI execution.
- Start through an ad-hoc CLI or one isolated research profile, not global MCP exposure.
- Run 2–3 real read-only tasks and record response quality, provider provenance, cost, latency, audit visibility, error behavior, and token revocation.
- Decide separately whether to keep catalog access, self-host a broker, or reject hosted credential storage.

## Source set from the worked example

- Repository: https://github.com/superdesigndev/treg
- README: https://github.com/superdesigndev/treg/blob/main/README.md
- Security model: https://github.com/superdesigndev/treg/blob/main/SECURITY.md
- Privacy policy source: https://github.com/superdesigndev/treg/blob/main/src/treg/web/privacy.html
- Terms source: https://github.com/superdesigndev/treg/blob/main/src/treg/web/terms.html
- Installer: https://github.com/superdesigndev/treg/blob/main/src/treg/web/install.sh
- License: https://github.com/superdesigndev/treg/blob/main/LICENSE
