---
name: memory-provider-setup
description: Guide to selecting, installing, and configuring Hermes memory providers. Covers all 8 providers with current status, dependencies, and migration advice.
version: 1.0.0
license: MIT
---

# Memory Provider Setup

Hermes supports external memory providers + built-in MEMORY.md/USER.md.

## Umbrella Scope: Hermes Memory Provider Configuration

This is the class-level memory-provider skill. Provider-specific setup notes belong here as subsections or references, not as standalone skills. The absorbed `hindsight-memory-setup` skill is preserved in `references/hindsight-memory-setup.md` and should be consulted when configuring Hindsight-specific environment variables, provider selection, and verification.

Use this skill for selecting providers, installing dependencies, editing Hermes memory config, verifying active provider status, and safely turning providers off without losing built-in memory. Only one external provider can be active at a time. The built-in memory always works alongside.

## Setup Commands

```bash
hermes memory setup    # interactive picker + configuration
hermes memory status   # check what's active
hermes memory off      # disable external provider
```

Or manually in config.yaml:
```yaml
memory:
  provider: holographic  # or honcho, mem0, hindsight, etc.
```

## Provider Comparison

### Holographic (RECOMMENDED - works day one)
| What | Local SQLite + FTS5 full-text search + HRR algebra |
| Deps | None (SQLite is Python stdlib). NumPy optional. |
| Storage | `$HERMES_HOME/memory_store.db` |
| Cost | Free |
| Tools | `fact_store` (9 actions: add/search/probe/related/reason/contradict/update/remove/list), `fact_feedback` |
| Setup | `hermes memory setup` → select "holographic". Zero config. |

**Unique:** Trust scoring (+0.05 helpful / -0.10 unhelpful), compositional queries (`reason`), conflict detection (`contradict`).

**Supplemental pattern for Karan's system:** do not replace the current Hindsight + standard memory + Obsidian + skills architecture just to experiment with Holographic. Use Holographic as a local staging, trust-scoring, contradiction-detection, and memory-quality-control layer for dream/closeout workflows. See `references/holographic-supplemental-memory-layer.md`.

### Hindsight
| What | Long-range semantic recall / memory provider used in some Hermes deployments |
| Status | Verify with `hermes memory status` before advising. Do not assume Hindsight is unavailable: in Karan's default profile it may be installed and active even if older notes mention dropped/changed upstream integration paths. |
| Package | Setup varies by integration path; prefer `hermes memory setup`, `hermes memory status`, and the Hindsight reference file over guessing pip package names. |
| Verdict | Keep Hindsight when it is already active and useful for cross-session/project recall; use Holographic as a supplement unless the user explicitly asks to migrate providers. |

### ByteRover
| What | Hierarchical knowledge tree + CLI with pre-compression extraction |
| Deps | `npm install -g byterover-cli` or `curl -fsSL https://byterover.dev/install.sh | sh` |
| Storage | `$HERMES_HOME/byterover/` (local) or cloud sync (optional) |
| Cost | Free (local), paid for cloud sync |
| Tools | `brv_query`, `brv_curate`, `brv_status` |
| Setup | Install brv CLI first, then `hermes memory setup` → select "byterover" |

### Honcho
| What | AI-native cross-session user modeling + dialectic Q&A |
| Deps | `pip install honcho-ai` + API key (honcho.dev) or self-hosted |
| Storage | Honcho Cloud or self-hosted |
| Cost | Paid (cloud) / free (self-hosted) |
| Tools | `honcho_profile`, `honcho_search`, `honcho_context`, `honcho_conclude` |
| Setup | `pip install honcho-ai`, then `hermes memory setup` → select "honcho" |
| Multi-agent | Each profile gets own Honcho peer, shared workspace |

### Other Providers (brief)
| Provider | Storage | Cost | Key Feature | Deps |
|----------|---------|------|-------------|------|
| Mem0 | Cloud | Paid | Server-side LLM extraction | `pip install mem0ai` |
| OpenViking | Self-hosted | Free | Filesystem hierarchy + tiered loading | `pip install openviking` + server |
| RetainDB | Cloud | $20/mo | Delta compression | API key |
| Supermemory | Cloud | Paid | Context fencing + graph ingest | `pip install supermemory` |

## Migration Strategy

When to migrate from Holographic to a knowledge-graph provider:
1. 10+ distinct entities with cross-references
2. Missing natural connections ("what did Amanda say about X vendor for Y client?")
3. Contradictions pile up (Holographic flags conflicts but can't synthesize)
4. Asking analytical questions, not just recall
5. Keyword search returns irrelevant results (need semantic retrieval)

## Troubleshooting
- Resolve the launcher's actual interpreter before checking packages. Modern source launchers can re-exec into a PM generation while `venv/bin/python` still points at an obsolete environment. Read the installation's PM `facts.json`; clear inherited `PYTHONPATH`/`PYTHONHOME` for package probes.
- On PM-managed Hermes, use reviewed `hermes plugins install <provider>` / enable admission for dependencies; do not repair the runtime with ad-hoc pip installs. Review consent and compare installed distributions before/after to catch unrelated changes.
- If interactive chat freezes at “Initializing agent…” and prints provider requirements, inspect `agent_init → memory_provider_migration.recover_at_startup → dashboard_install_plugin → publish_plugin → _consent_python_deps`. A missing formerly bundled provider can reach plain `input()` on the REPL worker while prompt_toolkit owns stdin. One-shot success does not prove memory is working: its non-TTY branch can skip installation and continue without the provider.
- Repair a missing configured provider explicitly outside the chat UI, keeping catalog pins, scanning, and dependency consent intact. Do not silently disable memory or auto-answer prompts without reviewing the requested install. See `references/hindsight-memory-setup.md` for local-external configuration.
- Verify two responses in ONE real interactive PTY, preferably over the reported SSH route, then verify active provider initialization and a real read-only recall. For automated typing, send text, pause at least 0.1 seconds, then send CR: the classic CLI treats Enter within 50ms of pasted text as a newline. `/quit` may print a session summary rather than “Goodbye”.
- `pip install hindsight` names an unrelated/broken package; don't use it.
- Launch a fresh CLI after dependency repair. Do not restart gateways or mutate other profiles without authorization.
