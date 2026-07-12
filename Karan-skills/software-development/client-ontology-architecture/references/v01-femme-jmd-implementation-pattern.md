# v0.1 Femme/JMD Ontology Implementation Pattern

Session-derived notes from implementing the first usable `sabnanikl-dev/client-ontologies` v0.1 system for Femme Events and JMD Menswear.

## What worked

- Build the validation foundation before ontology content:
  1. JSON Schema as documented contract.
  2. Deterministic validator script for repo-specific rules.
  3. Conventions doc for IDs/status/confidence/source types.
  4. Client modules and projections only after the shape is clear.
  5. SQLite export only after canonical YAML validates.

- Keep evidence source IDs local to each file/module. Reusing source IDs like `femme-local-seo-sot` across modules is useful and should not count as a global duplicate. Global duplicate checks should apply to ontology object IDs: client/module/entity/relationship/rule/projection/state-machine IDs.

- Namespaced lowercase IDs (`femme-events.website.site`, `jmd-menswear.inventory.image`) make projection cross-reference checks deterministic and avoid collisions.

- If Python YAML dependencies are unavailable, a practical fallback is Ruby stdlib YAML:
  `ruby -ryaml -rjson -e 'puts JSON.generate(YAML.load_file(ARGV[0]))' file.yaml`
  Do not hard-code newer Psych keyword args such as `aliases:` unless the local Ruby supports them.

- The validator should enforce more than parse/schema:
  - required fields by `kind`;
  - ID syntax and namespacing;
  - duplicate ontology object IDs;
  - relationship subject/object references;
  - projection module/entity/rule references;
  - evidence `source_id` references into the local file's source registry;
  - evidence required for active/approved/prohibited/verified facts and rules;
  - conservative secret-pattern scanning.

- SQLite runtime export can be simple but useful. Tables that covered v0.1 well:
  - `clients`
  - `modules`
  - `entities`
  - `relationships`
  - `rules`
  - `projections`
  - `sources`
  - `evidence`

## Pitfalls

- Running `python3 -m py_compile` creates `__pycache__`; add `__pycache__/` and `*.py[cod]` to `.gitignore` before committing or remove pycache before final commit.
- Generated SQLite outputs belong under ignored `build/`; do not commit runtime exports unless explicitly requested.
- Do not make source IDs globally unique in the validator; source registries are intentionally local to files.
- Do not mark draft operating plans as verified. For example, JMD inventory automation architecture may be source-backed as a draft plan, while specific future implementation decisions remain `draft`/`proposed`.
- If the user asks for commits but not push, commit locally and report branch ahead state; pushing is an external repo mutation that needs explicit approval.

## Verification checklist used

```bash
python3 scripts/validate_ontology.py
python3 -m py_compile scripts/validate_ontology.py scripts/export_sqlite.py
git diff --check
ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p) }' clients/*/client.yaml clients/*/modules/*.yaml clients/*/projections/*.yaml
python3 scripts/export_sqlite.py --output build/client-ontologies.sqlite
sqlite3 build/client-ontologies.sqlite 'select count(*) from clients; select count(*) from modules; select count(*) from entities; select count(*) from rules; select count(*) from projections;'
# plus a targeted secret regex scan excluding .git/build/__pycache__
```
