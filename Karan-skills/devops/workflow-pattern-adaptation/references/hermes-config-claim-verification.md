# Verifying Hermes config/behavior claims from external posts

Use this when a post, video, or clipped note claims "paste this into config.yaml" or explains how Hermes behaves. The goal is a verdict for each claim against the installed version, plus a decision on whether Karan should adopt it. Do not treat it as a summary.

## Procedure

1. **Extract the exact source.** Get the post text and the literal YAML, and number each claim (C1..Cn). Include the "why" claims (for example "plugin X disables Y"), not only the settings.
2. **Pin the version.** Record `hermes --version` and `git -C ~/.hermes/hermes-agent log -1 --format='%h %cd'`. Verdicts only apply to that commit.
3. **Map each key to code.** Run `grep -rn --include=*.py '\b<key>\b' agent hermes_cli`. Read the config parser (for compression, that is the settings builder in `agent/agent_init.py`) and `hermes_cli/config_defaults.py`. Note the **default applied when the key is absent**, because pasted YAML often differs from the defaults in ways the author never mentions.
4. **Test with real imports, not by reading.** Write a script that sets `HERMES_HOME` to a `tempfile.mkdtemp()` before importing Hermes modules. For each claim, build the real object (for example `ContextCompressor(..., model_thresholds=..., threshold_tokens_cap=..., provider=...)`), call the real recompute path (`update_model`), and assert on the numbers. Print a PASS/FAIL/PARTIAL line with its evidence for every claim. Run it with `~/.hermes/hermes-agent/venv/bin/python` from inside the hermes-agent directory. Template: `scripts/verify_compression_claims.py`.
5. **Mark partial truths as PARTIAL, not PASS.** If a claim is true only within limits (for example "kept verbatim" when there is a character budget and a per-message cap), report the actual limits.
6. **Compute Karan's current effective behaviour.** Read `~/.hermes/config.yaml` read-only and fill any absent keys from `DEFAULT_CONFIG`. Then compute the current effective value next to the post's proposed value. The usual finding is that the defaults already deliver most of the benefit.
7. **Diff the pasted YAML against the defaults.** Flag every key that disables a safety default. For example, an explicit `null` removes a default cap, and `in_place` flips the session-rotation mode. Say which models or routes get worse because of it.
8. **Separate offline-verifiable claims from live-only ones.** Allowance/cost savings, summary quality, and whether a provider accepts a large window need real calls that use quota. List them as unverified and offer a bounded live A/B, which needs approval.
9. **Live summariser A/B (after approval).**
   - **Cost gate first:** Karan does not want costs to go up. Before any call, pull live list prices from `https://openrouter.ai/api/v1/models` (prompt/completion/cache per M) for both candidates, and state whether the candidate is at or below the incumbent. Note which route is plan-included (Codex/ChatGPT OAuth) and which is paid per token (OpenRouter).
   - **Auth smoke test for each route:** `hermes chat -q 'Auth smoke test only. Reply with exactly: OK' --provider <p> --model <m> --toolsets '' --quiet`.
   - **Real input:** `hermes sessions export <out>.jsonl --format jsonl --newer-than 7d --min-messages 80`, then pick a large non-cron session.
   - **Identical prompt to both routes:** build `ContextCompressor`, replace `_call_summary_llm` with a function that captures the prompt, and call `_generate_summary(head_85pct)`. This gives exactly the prompt Hermes would send. Then send it once per route via `agent.auxiliary_client.call_llm(task="compression", provider=..., model=..., messages=..., reasoning_config=..., timeout=300)`. Record seconds, usage tokens, list-price $, and summary length. Save the prompt and both summaries to scratch. Template: `scripts/verify_compression_claims.py` (the offline harness; the live A/B follows the same import pattern).
   - **Faithfulness check, not only length:** `grep -c` distinctive facts from each summary (times, PIDs, hashes, numbers) against the captured prompt. A count of 0 means the model invented it. Also check that approval and non-action boundaries survived; cheaper or faster summarisers tend to drop them.
   - **Latency affects config:** if the winning model is slower than `auxiliary.compression.timeout` allows (reasoning models can take about 2 minutes on a ~40K-token prompt), include a timeout raise in the recommendation.
   - **Window check:** a summariser whose window is at or above the effective trigger does not need a large-context variant (e.g. a `-900k` suffix). Only recommend the variant when the window would cap the trigger.
   - **Report shape:** cost verdict first (against the no-increase condition), then quality with concrete invented or dropped items, then speed, then the minimal YAML diff, marked not applied. Back up `config.yaml` and apply only after an explicit approval.

## Report shape (Telegram)

- The bottom line first: whether the mechanics are real and whether Karan needs the config.
- The PASS list with concrete numbers, then PARTIAL, then "matters for you" (current effective settings vs proposed), then traps in the pasted YAML, then what can't be verified offline.
- Recommend minimal adoption (only the keys that add value), or none.
- End with what was not mutated (live config, auth, vault) and the path to the re-runnable script.

## Pitfalls

- Never paste a post's YAML wholesale. Keys set to `null` or to non-default booleans silently override protective defaults, and the author's setup may not share your defaults.
- A harness that constructs objects with the default `threshold_tokens_cap=None` does not match live behaviour, because the config loader injects the `DEFAULT_CONFIG` cap when the key is absent. Compute the live value with the defaults merged in, or the report will be wrong.
- Tests that depend on provider identity (for example a durable ceiling that is kept only when the runtime is unchanged) must pass the same provider string across calls. A placeholder provider makes the code treat it as a runtime switch and produces a false FAIL.
- Keep Karan OS notes read-only unless the current turn asks for capture. Offer a "Verification" section as a next step instead. If the vault guard blocks a requested write, do not work around it. Draft the section in scratch, give its path, and ask Karan to confirm with a phrase naming the exact note.
- Scripts run through the terminal tool can end up under a different interpreter that lacks the venv's packages. `-c` works but `script.py` fails with `ModuleNotFoundError: ruamel`. Make harness scripts self-contained by calling `site.addsitedir("~/.hermes/hermes-agent/venv/lib/python3.11/site-packages")` (expanded) and inserting the hermes-agent path at the top, rather than retrying different launch commands.
- Do not judge a summariser by length or speed. A compact summary can invent timestamps and drop authority boundaries, so check each distinctive fact against the source prompt.
