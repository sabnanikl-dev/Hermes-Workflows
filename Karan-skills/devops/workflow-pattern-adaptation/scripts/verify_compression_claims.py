"""Offline verification harness for Hermes compression config claims.
Real imports, temp HERMES_HOME, no network, no writes to live config.
Run: cd ~/.hermes/hermes-agent && ./venv/bin/python <this file>
Edit MT / MODELS / PRV for the claims under test."""
import os, sys, tempfile, json, types
os.environ["HERMES_HOME"] = tempfile.mkdtemp(prefix="hh-")
sys.path.insert(0, os.path.expanduser("~/.hermes/hermes-agent"))

from agent.context_compressor import ContextCompressor, resolve_model_threshold
from agent.model_metadata import get_model_context_length
from agent import conversation_compression as cc
from hermes_cli.config_defaults import DEFAULT_CONFIG  # noqa: may live elsewhere; adjust if import fails

PRV = "claude-subscription-directsdk-experimental"
MT = {"claude-opus": 0.25, "gpt-6": 0.85}
out = []
def rec(cid, ok, ev): out.append((cid, ok, ev))

def trig(model, ctx, provider, mt=MT, default=0.5, cap=None):
    c = ContextCompressor(model=model, threshold_percent=default, model_thresholds=mt,
                          threshold_tokens_cap=cap, provider=provider,
                          config_context_length=ctx, quiet_mode=True)
    c.update_model(model, ctx, provider=provider)
    return c

rec("per-model pct", None, {m: resolve_model_threshold(m, MT, 0.5, p) for m, p in
    [("claude-opus-5-5", PRV), ("gpt-6-luna", "openai-codex"), ("claude-sonnet-5", PRV)]})
rec("opus 1M trigger", None, trig("claude-opus-5-5", 1_000_000, PRV).threshold_tokens)
rec("codex windows", None, {m: get_model_context_length(m, provider="openai-codex")
                             for m in ("gpt-6-luna", "gpt-6-luna-900k")})

# Aux summariser ceiling: same provider string across calls (a different one = runtime switch).
c = trig("claude-opus-5-5", 1_000_000, PRV, mt={})
before = c.threshold_tokens
ag = types.SimpleNamespace(context_compressor=c, model="claude-opus-5-5", provider=PRV,
                           _compression_warning=None, _emit_diagnostic_status=lambda m: None)
cc._lower_threshold_to_aux_context(ag, aux_model="gpt-6-luna", aux_context=272_000,
                                   aux_provider="openai-codex", aux_base_url="")
c.update_model("claude-opus-5-5", 1_000_000, provider=PRV)
rec("aux ceiling durable", c.threshold_tokens == 272_000, (before, c.threshold_tokens))

# Live effective vs proposed: merge DEFAULT_CONFIG for absent keys.
import yaml
live = (yaml.safe_load(open(os.path.expanduser("~/.hermes/config.yaml"))) or {}).get("compression", {})
dflt = DEFAULT_CONFIG.get("compression", {})
cap = live.get("threshold_tokens", dflt.get("threshold_tokens"))
rec("LIVE opus trigger", None, trig("claude-opus-5-5", 1_000_000, PRV,
    mt=live.get("model_thresholds") or {}, default=float(live.get("threshold", 0.5)), cap=cap).threshold_tokens)
rec("PROPOSED opus trigger", None, trig("claude-opus-5-5", 1_000_000, PRV, cap=None).threshold_tokens)
rec("PROPOSED unlisted-model trigger (cap removed)", None,
    trig("claude-sonnet-5", 1_000_000, PRV, cap=None).threshold_tokens)

for cid, ok, ev in out:
    print(cid, "INFO" if ok is None else ("PASS" if ok else "FAIL"), "|", ev)
