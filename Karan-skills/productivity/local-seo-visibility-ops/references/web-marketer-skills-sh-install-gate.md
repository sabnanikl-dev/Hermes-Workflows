# Web Marketer skills.sh Install Gate

Use this when a local-SEO/web-marketing profile has a Linear or tracker approval to install community `skills.sh` skills.

## Pattern

1. Verify the tracker issue/comment first; do not infer approval from memory.
2. Install into the target profile only, e.g. `hermes -p web-marketer skills install <skill-id>`.
3. Community installs may still prompt even after scan approval. For scanner-allowed skills, pipe an explicit confirmation if automating:
   ```bash
   printf 'y\n' | hermes -p web-marketer skills install '<skill-id>'
   ```
4. Treat scan overrides as a separate approval boundary:
   - `SAFE` + allowed: install if the user/tracker approved the skill.
   - `CAUTION` + blocked: do not use `--force` unless Karan/default Hermes explicitly approves overriding the scanner for that exact skill.
   - `DANGEROUS` + blocked: same, but call out the higher risk and prefer rejection unless there is a strong reason.
5. After installs, verify all three layers:
   - profile isolation marker such as `.no-bundled-skills` still exists;
   - `find <profile>/skills -name SKILL.md` or `hermes -p <profile> skills list` shows only expected additions;
   - profile smoke test still works with the intended provider/model.
6. Update the tracker with installed skills, blocked skills, and verification output. Do not report blocked skills as installed.

## Why this exists

In the `web-marketer` setup, PAPI-58 approved several community SEO skills. Three safe skills installed cleanly after explicit confirmation, while `firecrawl-seo-audit` was blocked as `CAUTION` and `ai-seo` as `DANGEROUS`. The durable lesson is the approval split: user approval to install community skills is not automatically approval to override Hermes' skill scanner.