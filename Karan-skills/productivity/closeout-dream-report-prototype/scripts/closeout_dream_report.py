#!/usr/bin/env python3
"""Read-only Hermes closeout/dream report generator.

Collects recent Hermes sessions, optional GitHub merged PRs, and optional Linear
completed issues, then generates a self-contained HTML memory-routing report.
No memory, Hindsight, Obsidian, Linear, or GitHub writes are performed.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import textwrap
import time
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
STATE_DB = HERMES_HOME / "state.db"
OUTPUT_DIR = HERMES_HOME / "reports" / "closeout-dream"
HISTORY_PATH = OUTPUT_DIR / "candidate-pattern-history.json"
CONFIG_PATH = HERMES_HOME / "config.yaml"

NOISE_PATTERNS = [
    r"\bPR #?\d+\b",
    r"\bissue #?\d+\b",
    r"\bcommit [0-9a-f]{7,}\b",
    r"\bPhase \d+\b",
    r"\btoday\b",
]
PREFERENCE_PATTERNS = [
    r"\bprefer(?:s|red)?\b",
    r"\bwants?\b",
    r"\blikes?\b",
    r"\bexpects?\b",
    r"\bremember(?: this)?\b",
    r"\bsaved the durable preference\b",
]
WORKFLOW_PATTERNS = [
    r"\bverify\b",
    r"\bguardrail\b",
    r"\bskill\b",
    r"\bworkflow\b",
    r"\bpitfall\b",
    r"\bapproval\b",
    r"\bsource[- ]of[- ]truth\b",
]
PROJECT_PATTERNS = [
    r"\bFemme\b",
    r"\bPapi\b",
    r"\bJMD\b",
    r"\bHermes Brain\b",
    r"\bLinear\b",
    r"\bGitHub\b",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate read-only Hermes closeout dream HTML report")
    p.add_argument("--since", default="7d", help="Lookback window, e.g. 24h, 7d, 14d")
    p.add_argument("--output", default="", help="Output HTML path; default under ~/.hermes/reports/closeout-dream/")
    p.add_argument("--json-output", default="", help="Optional raw JSON output path")
    p.add_argument("--max-sessions", type=int, default=40)
    p.add_argument("--max-messages-per-session", type=int, default=18)
    p.add_argument("--dry-run", action="store_true", default=True, help="Always read-only; kept for command clarity")
    p.add_argument("--update-history", action="store_true", help="Update pattern history. Use for scheduled runs; omit for manual tests to avoid artificial maturation.")
    return p.parse_args()


def parse_since(value: str) -> tuple[datetime, str]:
    now = datetime.now(timezone.utc)
    m = re.fullmatch(r"(\d+)([hdw])", value.strip().lower())
    if not m:
        raise SystemExit("--since must look like 24h, 7d, or 2w")
    n = int(m.group(1)); unit = m.group(2)
    delta = {"h": timedelta(hours=n), "d": timedelta(days=n), "w": timedelta(weeks=n)}[unit]
    return now - delta, value


def load_dotenv_keys() -> None:
    # Load only keys missing from process env. Do not print values.
    env_path = HERMES_HOME / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def ts_to_iso(ts: float | int | None) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(s: str, limit: int = 360) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    s = re.sub(r"MEDIA:/\S+", "[media attachment]", s)
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return s


def detect_memory_backend() -> dict[str, Any]:
    """Detect the active Hermes memory backend without importing Hermes internals.

    The report is read-only, but backend awareness matters for routing language:
    built-in memory is compact prompt-injected state, Holographic is local
    trust-scored/entity-bound fact storage, and Hindsight is structured
    cross-session/entity/temporal memory.
    """
    provider = ""
    plugin_wired = False
    if CONFIG_PATH.exists():
        lines = CONFIG_PATH.read_text(errors="ignore").splitlines()
        in_memory = False
        memory_indent = None
        for raw in lines:
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if re.match(r"^memory\s*:", raw):
                in_memory = True
                memory_indent = indent
                continue
            if in_memory and memory_indent is not None and indent <= memory_indent and re.match(r"^[A-Za-z0-9_-]+\s*:", raw):
                in_memory = False
            if in_memory and stripped.startswith("provider:"):
                provider = stripped.split(":", 1)[1].strip().strip("'\"")
            if "hermes-memory-store" in stripped:
                plugin_wired = True
    mode = (provider or "built-in").lower()
    notes = []
    if mode == "holographic":
        label = "Holographic staging"
        if not plugin_wired:
            notes.append("holographic configured but hermes-memory-store plugin section was not detected; promotion tooling may be unavailable")
    elif mode == "hindsight":
        label = "Hindsight-aware staging"
        notes.append("Hindsight is strongest for structured entity/temporal/shared recall; keep compact preferences in standard memory and procedures in skills")
    elif mode in {"honcho", "mem0"}:
        label = "Memory-backend-aware staging"
        notes.append(f"{mode} provider detected; this prototype stages only and treats promotion as approval-gated backend-specific work")
    else:
        label = "Built-in memory staging"
    return {"provider": provider or "built-in", "mode": mode, "staging_label": label, "plugin_wired": plugin_wired, "notes": notes}


def staging_route(prefix: str, backend: dict[str, Any]) -> str:
    if backend.get("mode") == "holographic":
        return f"Holographic staging: {prefix}"
    if backend.get("mode") == "hindsight":
        return f"Hindsight-aware staging: {prefix}"
    return f"Staging: {prefix}"


def query_sessions(since: datetime, max_sessions: int, max_messages: int) -> list[dict[str, Any]]:
    if not STATE_DB.exists():
        return []
    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    since_ts = since.timestamp()
    sessions = conn.execute(
        """
        SELECT id, source, model, started_at, ended_at, message_count, tool_call_count
        FROM sessions
        WHERE started_at >= ?
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (since_ts, max_sessions),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for s in sessions:
        msgs = conn.execute(
            """
            SELECT id, role, content, tool_name, timestamp
            FROM messages
            WHERE session_id = ? AND role IN ('user','assistant') AND COALESCE(content,'') <> ''
            ORDER BY timestamp ASC
            """,
            (s["id"],),
        ).fetchall()
        picked = []
        # Keep first/last plus any messages with signal words.
        signal_idxs = set()
        for i, m in enumerate(msgs):
            c = m["content"] or ""
            if any(re.search(p, c, re.I) for p in PREFERENCE_PATTERNS + WORKFLOW_PATTERNS + PROJECT_PATTERNS):
                signal_idxs.add(i)
        for i in sorted(set(list(range(min(3, len(msgs)))) + list(range(max(0, len(msgs)-3), len(msgs))) + list(signal_idxs))):
            if len(picked) >= max_messages:
                break
            m = msgs[i]
            picked.append({
                "role": m["role"],
                "content": clean_text(m["content"], 420),
                "timestamp": ts_to_iso(m["timestamp"]),
            })
        title = picked[0]["content"] if picked else s["id"]
        out.append({
            "id": s["id"],
            "source": s["source"],
            "model": s["model"],
            "started_at": ts_to_iso(s["started_at"]),
            "message_count": s["message_count"],
            "tool_call_count": s["tool_call_count"],
            "title": clean_text(title, 96),
            "messages": picked,
        })
    return out


def run_json_command(cmd: list[str], timeout: int = 30) -> tuple[bool, Any, str]:
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        return False, None, str(e)
    if cp.returncode != 0:
        return False, None, clean_text(cp.stderr or cp.stdout, 700)
    try:
        return True, json.loads(cp.stdout or "[]"), ""
    except Exception as e:
        return False, None, f"JSON parse failed: {e}"


def collect_github(since: datetime) -> dict[str, Any]:
    if not shutil.which("gh"):
        return {"available": False, "items": [], "error": "gh CLI not installed"}
    date = since.date().isoformat()
    # gh search accepts a GitHub search query. author:@me works with authenticated gh.
    cmd = [
        "gh", "search", "prs",
        f"author:@me", f"merged:>={date}", "--merged",
        "--json", "title,url,repository,closedAt,state,author",
        "--limit", "30",
    ]
    ok, data, err = run_json_command(cmd, timeout=45)
    if not ok:
        return {"available": False, "items": [], "error": err}
    items = []
    for pr in data or []:
        repo = pr.get("repository") or {}
        items.append({
            "title": pr.get("title", ""),
            "url": pr.get("url", ""),
            "repo": repo.get("nameWithOwner") or repo.get("fullName") or repo.get("name") or "",
            "merged_at": pr.get("closedAt", ""),
            "state": pr.get("state", ""),
        })
    return {"available": True, "items": items, "error": ""}


def collect_linear(since: datetime) -> dict[str, Any]:
    token = os.environ.get("LINEAR_API_KEY")
    if not token:
        return {"available": False, "items": [], "error": "LINEAR_API_KEY not present in environment/.env"}
    query = """
    query CloseoutIssues($updatedAt: DateTimeOrDuration!) {
      issues(first: 50, filter: {updatedAt: {gte: $updatedAt}}) {
        nodes { identifier title url updatedAt completedAt state { name type } project { name } team { key name } }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"updatedAt": since.isoformat().replace("+00:00", "Z")}}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return {"available": False, "items": [], "error": clean_text(str(e), 500)}
    if data.get("errors"):
        return {"available": False, "items": [], "error": clean_text(json.dumps(data["errors"]), 700)}
    items = []
    for issue in (((data.get("data") or {}).get("issues") or {}).get("nodes") or []):
        state_type = ((issue.get("state") or {}).get("type") or "")
        if state_type not in {"completed", "canceled"}:
            continue
        items.append({
            "identifier": issue.get("identifier", ""),
            "title": issue.get("title", ""),
            "url": issue.get("url", ""),
            "state": ((issue.get("state") or {}).get("name") or ""),
            "state_type": ((issue.get("state") or {}).get("type") or ""),
            "team": ((issue.get("team") or {}).get("key") or ""),
            "project": ((issue.get("project") or {}).get("name") or ""),
            "completed_at": issue.get("completedAt") or issue.get("updatedAt") or "",
        })
    return {"available": True, "items": items, "error": ""}


def route_for(text: str, backend: dict[str, Any]) -> tuple[str, float, str]:
    """Initial, conservative single-run route.

    One sighting is *not* enough to recommend durable memory. The nightly
    history pass later raises trust only when the same pattern recurs across
    dreams/sources.
    """
    preference = any(re.search(p, text, re.I) for p in PREFERENCE_PATTERNS)
    workflow = any(re.search(p, text, re.I) for p in WORKFLOW_PATTERNS)
    project = any(re.search(p, text, re.I) for p in PROJECT_PATTERNS)
    noise = any(re.search(p, text, re.I) for p in NOISE_PATTERNS)
    if noise:
        return "No-op / source-of-truth only", 0.18, "Looks like temporary task state or external tracker detail."
    if workflow and not preference:
        return staging_route("possible skill pattern", backend), 0.38, "One procedural observation is not enough; repeat across dreams before recommending a skill patch."
    if preference:
        return staging_route("possible standard-memory pattern", backend), 0.40, "One preference-like observation should stage low until repeated evidence confirms it."
    if project:
        if backend.get("mode") == "hindsight":
            return "Hindsight staging: possible entity/project/temporal pattern", 0.34, "Project context may belong in Hindsight or Obsidian, but needs recurrence before promotion."
        return staging_route("possible wiki/Hindsight pattern", backend), 0.34, "Project context may become useful, but needs recurrence before promotion."
    return staging_route("unclassified signal", backend), 0.28, "Potential signal, but needs repeated evidence before promotion."


def candidate_fingerprint(text: str) -> str:
    """Coarse fingerprint for recognizing recurring memory patterns.

    This intentionally collapses task-specific numbers/URLs and common filler so
    repeated ideas strengthen while one-off tracker facts stay weak.
    """
    t = text.lower()
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\b(?:pr|issue|papi|jmd)-?#?\d+\b", " ", t)
    t = re.sub(r"\b\d{4}-\d{2}-\d{2}\b|\b\d+\b", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    stop = {
        "the", "and", "for", "that", "this", "with", "from", "into", "should", "would", "could",
        "want", "wants", "requested", "assistant", "user", "karan", "hermes", "report", "review",
        "task", "issue", "pull", "request", "recent", "today", "done", "completed",
    }
    words = [w for w in t.split() if len(w) > 3 and w not in stop]
    return " ".join(words[:18]) or re.sub(r"\W+", " ", text.lower())[:80]


def load_pattern_history() -> dict[str, Any]:
    if not HISTORY_PATH.exists():
        return {"patterns": {}}
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"patterns": {}}


def apply_pattern_history(candidates: list[dict[str, Any]], history: dict[str, Any], *, write_history: bool = False) -> list[dict[str, Any]]:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    patterns = history.setdefault("patterns", {})
    for c in candidates:
        fp = candidate_fingerprint(c.get("candidate", ""))
        c["pattern_key"] = fp
        p = patterns.setdefault(fp, {
            "first_seen": now,
            "last_seen": now,
            "dream_count": 0,
            "sources": [],
            "routes": [],
            "examples": [],
        })
        evidence_key = f"{c.get('source_type','')}:{c.get('source','')}:{fp}"
        evidence_keys = p.setdefault("evidence_keys", [])
        is_new_evidence = evidence_key not in evidence_keys
        if is_new_evidence:
            evidence_keys.append(evidence_key)
            p["dream_count"] = int(p.get("dream_count", 0)) + 1
        p["last_seen"] = now
        p["run_seen_count"] = int(p.get("run_seen_count", 0)) + 1
        if c.get("source_type") not in p.setdefault("sources", []):
            p["sources"].append(c.get("source_type"))
        if c.get("route") not in p.setdefault("routes", []):
            p["routes"].append(c.get("route"))
        examples = p.setdefault("examples", [])
        example = clean_text(c.get("candidate", ""), 180)
        if example and example not in examples:
            examples.append(example)
            del examples[:-3]

        observations = max(1, len(p.get("evidence_keys", [])))
        source_diversity = len(p.get("sources", []))
        base = float(c.get("trust", 0.0))
        repeat_boost = min(0.34, max(0, observations - 1) * 0.08)
        diversity_boost = min(0.10, max(0, source_diversity - 1) * 0.05)
        score = min(0.88, base + repeat_boost + diversity_boost)

        # Promotion thresholds are pattern-first, not one-off-first.
        if c.get("route", "").startswith("No-op"):
            c["trust"] = round(min(score, 0.30), 2)
            c["promotion_readiness"] = "source-truth only"
        elif observations >= 5 and score >= 0.72:
            c["trust"] = round(score, 2)
            if "skill" in c["route"].lower():
                c["route"] = "Skill recommendation"
            elif "wiki" in c["route"].lower() or "hindsight" in c["route"].lower():
                c["route"] = "Obsidian/Hindsight recommendation"
            else:
                c["route"] = "Standard memory recommendation"
            c["promotion_readiness"] = "ready for approval"
        elif observations >= 3 and score >= 0.56:
            c["trust"] = round(score, 2)
            c["promotion_readiness"] = "emerging pattern"
        else:
            c["trust"] = round(score, 2)
            c["promotion_readiness"] = "needs more dreams"

        c["pattern_observations"] = observations
        c["pattern_sources"] = source_diversity
        c["rationale"] = (
            f"{c.get('rationale', '')} Pattern has {observations} unique evidence observation(s) across {source_diversity} source type(s); "
            f"promotion waits for distinct repeated evidence, not repeated manual runs."
        )
    if write_history:
        HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return candidates


def extract_candidates(sessions: list[dict[str, Any]], github: dict[str, Any], linear: dict[str, Any], backend: dict[str, Any]) -> list[dict[str, Any]]:
    session_candidates: list[dict[str, Any]] = []
    tracker_candidates: list[dict[str, Any]] = []
    seen = set()
    for s in sessions:
        for m in s.get("messages", []):
            content = m.get("content", "")
            if not content or len(content) < 35:
                continue
            if content.lstrip().startswith("[IMPORTANT:") or "has invoked the" in content[:180]:
                continue
            if not any(re.search(p, content, re.I) for p in PREFERENCE_PATTERNS + WORKFLOW_PATTERNS + PROJECT_PATTERNS + NOISE_PATTERNS):
                continue
            route, trust, rationale = route_for(content, backend)
            key = re.sub(r"\W+", " ", content.lower())[:120]
            if key in seen:
                continue
            seen.add(key)
            session_candidates.append({
                "candidate": content,
                "route": route,
                "trust": round(trust, 2),
                "rationale": rationale,
                "source_type": "Hermes session",
                "source": s["id"],
                "timestamp": m.get("timestamp", s.get("started_at", "")),
            })
    for pr in github.get("items", [])[:12]:
        text = f"Merged GitHub PR in {pr.get('repo')}: {pr.get('title')}"
        tracker_candidates.append({
            "candidate": text,
            "route": "No-op / source-of-truth only",
            "trust": 0.25,
            "rationale": "Merged PRs are implementation evidence; only promote if they reveal a reusable workflow lesson.",
            "source_type": "GitHub PR",
            "source": pr.get("url", ""),
            "timestamp": pr.get("merged_at", ""),
        })
    for issue in linear.get("items", [])[:12]:
        text = f"Completed Linear issue {issue.get('identifier')}: {issue.get('title')}"
        tracker_candidates.append({
            "candidate": text,
            "route": "No-op / source-of-truth only",
            "trust": 0.24,
            "rationale": "Linear is task truth; avoid duplicating issue status into memory unless it encodes durable project context.",
            "source_type": "Linear issue",
            "source": issue.get("url", ""),
            "timestamp": issue.get("completed_at", ""),
        })
    session_candidates.sort(key=lambda c: (c["trust"], c["timestamp"]), reverse=True)
    tracker_candidates.sort(key=lambda c: (c["timestamp"], c["source_type"]), reverse=True)
    return session_candidates[:24] + tracker_candidates[:12]


def summarize(sessions: list[dict[str, Any]], github: dict[str, Any], linear: dict[str, Any], candidates: list[dict[str, Any]], backend: dict[str, Any]) -> dict[str, Any]:
    routes = Counter(c["route"] for c in candidates)
    source_counts = Counter(c["source_type"] for c in candidates)
    promote = sum(1 for c in candidates if c.get("promotion_readiness") == "ready for approval")
    staged = sum(1 for c in candidates if c.get("promotion_readiness") in {"needs more dreams", "emerging pattern"})
    emerging = sum(1 for c in candidates if c.get("promotion_readiness") == "emerging pattern")
    ignored = sum(1 for c in candidates if c.get("promotion_readiness") == "source-truth only" or c["route"].startswith("No-op"))
    return {
        "sessions_seen": len(sessions),
        "github_seen": len(github.get("items", [])),
        "linear_seen": len(linear.get("items", [])),
        "candidate_count": len(candidates),
        "promote_count": promote,
        "stage_count": staged,
        "emerging_count": emerging,
        "ignore_count": ignored,
        "routes": dict(routes),
        "sources": dict(source_counts),
        "memory_backend": backend.get("provider", "built-in"),
        "staging_label": backend.get("staging_label", "Memory staging"),
    }


def esc(s: Any) -> str:
    return html.escape(str(s or ""), quote=True)


def pct(v: float) -> str:
    return f"{max(0, min(100, v * 100)):.0f}%"


def render_svg_architecture(summary: dict[str, Any]) -> str:
    return f"""
    <svg viewBox="0 0 1080 380" role="img" aria-label="Closeout architecture diagram">
      <defs>
        <linearGradient id="g1" x1="0" x2="1"><stop stop-color="#9ec7ff"/><stop offset="1" stop-color="#d9c3ff"/></linearGradient>
        <linearGradient id="g2" x1="0" x2="1"><stop stop-color="#fff1b8"/><stop offset="1" stop-color="#f4b9cf"/></linearGradient>
        <filter id="shadow"><feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#3a214f" flood-opacity="0.16"/></filter>
      </defs>
      <rect width="1080" height="380" rx="34" fill="#fffaf7"/>
      <g font-family="Inter, system-ui" font-weight="800" fill="#3a214f" text-anchor="middle">
        <rect x="42" y="60" width="160" height="82" rx="24" fill="#eef6ff" filter="url(#shadow)"/><text x="122" y="96">Sessions</text><text x="122" y="122" font-size="22">{summary['sessions_seen']}</text>
        <rect x="42" y="154" width="160" height="82" rx="24" fill="#f5e9ff" filter="url(#shadow)"/><text x="122" y="190">GitHub PRs</text><text x="122" y="216" font-size="22">{summary['github_seen']}</text>
        <rect x="42" y="248" width="160" height="82" rx="24" fill="#fff1b8" filter="url(#shadow)"/><text x="122" y="284">Linear Issues</text><text x="122" y="310" font-size="22">{summary['linear_seen']}</text>
        <path d="M222 101 C300 101 304 190 382 190" stroke="#7e57c2" stroke-width="4" fill="none" marker-end="url(#arrow)"/>
        <path d="M222 195 C300 195 304 190 382 190" stroke="#7e57c2" stroke-width="4" fill="none"/>
        <path d="M222 289 C300 289 304 190 382 190" stroke="#7e57c2" stroke-width="4" fill="none"/>
        <rect x="382" y="118" width="250" height="144" rx="30" fill="url(#g1)" filter="url(#shadow)"/>
        <text x="507" y="172" font-size="22">{esc(summary.get('staging_label', 'Memory staging'))}</text><text x="507" y="206" font-size="34">{summary['candidate_count']} candidates</text><text x="507" y="232" font-size="15" font-weight="650">trust · evidence · route</text>
        <path d="M648 190 C704 190 706 92 766 92" stroke="#7e57c2" stroke-width="4" fill="none"/>
        <path d="M648 190 C704 190 706 190 766 190" stroke="#7e57c2" stroke-width="4" fill="none"/>
        <path d="M648 190 C704 190 706 288 766 288" stroke="#7e57c2" stroke-width="4" fill="none"/>
        <rect x="766" y="52" width="250" height="78" rx="24" fill="#fff" stroke="#d9c3ff"/><text x="891" y="86">Promote after approval</text><text x="891" y="112" font-size="22">{summary['promote_count']}</text>
        <rect x="766" y="151" width="250" height="78" rx="24" fill="#fff" stroke="#d9c3ff"/><text x="891" y="185">Keep staged</text><text x="891" y="211" font-size="22">{summary['stage_count']}</text>
        <rect x="766" y="250" width="250" height="78" rx="24" fill="#fff" stroke="#d9c3ff"/><text x="891" y="284">Ignore / source truth</text><text x="891" y="310" font-size="22">{summary['ignore_count']}</text>
      </g>
    </svg>"""


def render_candidate(c: dict[str, Any]) -> str:
    route_class = re.sub(r"[^a-z0-9]+", "-", c["route"].lower()).strip("-")
    bar = pct(float(c.get("trust", 0)))
    source = c.get("source", "")
    source_html = f'<a href="{esc(source)}">source</a>' if str(source).startswith("http") else esc(source)
    return f"""
      <article class="candidate {route_class}">
        <div class="candidate-top"><span>{esc(c['route'])}</span><strong>{esc(c['trust'])}</strong></div>
        <p>{esc(c['candidate'])}</p>
        <div class="trust"><i style="width:{bar}"></i></div>
        <footer><span>{esc(c['source_type'])}</span><span>{source_html}</span></footer>
        <small>{esc(c['rationale'])}</small>
        <small><b>Pattern:</b> {esc(c.get('promotion_readiness', 'needs more dreams'))} · {esc(c.get('pattern_observations', 1))} dream observation(s) · {esc(c.get('pattern_sources', 1))} source type(s)</small>
      </article>
    """


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    routes = summary.get("routes", {})
    route_rows = "".join(f"<li><b>{esc(k)}</b><span>{v}</span></li>" for k, v in sorted(routes.items(), key=lambda kv: kv[1], reverse=True))
    candidates = report["candidates"]
    top_candidates = "".join(render_candidate(c) for c in candidates[:18]) or "<p>No candidates found in this window.</p>"
    source_notes = []
    backend = report.get("backend", {})
    source_notes.append(f"<li><b>Memory backend</b><span>{esc(backend.get('provider', 'built-in'))} · {esc(backend.get('staging_label', 'Memory staging'))}</span></li>")
    for note in backend.get("notes", []):
        source_notes.append(f"<li><b>Backend note</b><span>{esc(note)}</span></li>")
    for name in ["github", "linear"]:
        src = report.get(name, {})
        if not src.get("available"):
            source_notes.append(f"<li><b>{name.title()}</b><span>{esc(src.get('error', 'Unavailable'))}</span></li>")
    source_notes_html = "".join(source_notes) or "<li><b>All optional sources</b><span>Available for this dry run.</span></li>"
    arch = render_svg_architecture(summary)
    generated = esc(report["generated_at"])
    since = esc(report["since"])
    json_name = esc(Path(report.get("json_path", "")).name)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Hermes Closeout Dream Report</title>
<style>
:root {{ --ink:#22182f; --soft:#62546f; --muted:#897a98; --paper:#fffaf7; --mist:#f5e9ff; --lilac:#d9c3ff; --rose:#f4b9cf; --moon:#fff1b8; --blue:#9ec7ff; --violet:#7e57c2; --plum:#3a214f; --line:rgba(88,62,122,.17); --shadow:0 24px 70px rgba(58,33,79,.16); }}
*{{box-sizing:border-box}} body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:radial-gradient(circle at 12% 4%,rgba(255,241,184,.72),transparent 24rem),radial-gradient(circle at 84% 8%,rgba(158,199,255,.66),transparent 24rem),linear-gradient(135deg,#fffaf7 0%,#f5e9ff 48%,#eef6ff 100%);}} a{{color:#6541a8}} .shell{{max-width:1180px;margin:0 auto;padding:38px 22px 64px}} .hero{{padding:46px;border:1px solid var(--line);border-radius:38px;background:rgba(255,255,255,.55);box-shadow:var(--shadow);overflow:hidden;position:relative}} .hero:after{{content:"";position:absolute;right:-90px;top:-90px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(126,87,194,.16),transparent 68%)}} .eyebrow{{margin:0 0 12px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#7e57c2;font-size:.78rem}} h1{{font-size:clamp(2.4rem,7vw,5.8rem);line-height:.92;margin:0;letter-spacing:-.07em}} h2{{font-size:clamp(1.7rem,4vw,3.1rem);line-height:1;margin:0;letter-spacing:-.04em}} h3{{margin:0 0 8px;font-size:1.1rem}} .lede{{max-width:820px;color:var(--soft);font-size:1.14rem;line-height:1.7}} .meta{{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}} .pill{{padding:10px 14px;border-radius:999px;background:white;border:1px solid var(--line);font-weight:800;color:var(--plum)}} .section{{margin-top:28px;padding:32px;border:1px solid var(--line);border-radius:32px;background:rgba(255,255,255,.58);box-shadow:0 14px 42px rgba(58,33,79,.08)}} .metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:22px}} .metric{{padding:22px;border-radius:24px;background:white;border:1px solid var(--line)}} .metric strong{{display:block;font-size:2.2rem;letter-spacing:-.05em}} .metric span{{color:var(--soft);font-weight:750}} .diagram{{margin-top:22px;border-radius:34px;overflow:hidden;border:1px solid var(--line);background:white}} .split{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .route-list,.notes{{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:10px}} .route-list li,.notes li{{display:flex;justify-content:space-between;gap:12px;padding:14px 16px;border-radius:18px;background:white;border:1px solid var(--line)}} .route-list span,.notes span{{color:var(--soft)}} .candidate-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:22px}} .candidate{{padding:18px;border-radius:24px;background:white;border:1px solid var(--line);box-shadow:0 12px 28px rgba(58,33,79,.07)}} .candidate p{{min-height:84px;color:var(--ink);line-height:1.48;margin:10px 0 14px}} .candidate small{{display:block;color:var(--soft);line-height:1.45;margin-top:10px}} .candidate-top{{display:flex;align-items:center;justify-content:space-between;gap:10px}} .candidate-top span{{font-weight:900;font-size:.78rem;letter-spacing:.05em;text-transform:uppercase;color:#7e57c2}} .candidate-top strong{{padding:6px 9px;border-radius:999px;background:#f5e9ff}} .trust{{height:9px;border-radius:999px;background:#eee7f5;overflow:hidden}} .trust i{{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--blue),var(--violet),var(--rose))}} footer{{display:flex;justify-content:space-between;gap:10px;margin-top:10px;font-size:.82rem;color:var(--muted)}} .decision{{display:grid;grid-template-columns:1.2fr .8fr;gap:18px;align-items:stretch}} .box{{padding:22px;border-radius:24px;background:white;border:1px solid var(--line)}} code{{background:#20152f;color:#f7efff;padding:.2em .42em;border-radius:8px}} .final-note{{color:var(--soft);font-size:.95rem;line-height:1.55}} @media(max-width:900px){{.metrics,.split,.candidate-grid,.decision{{grid-template-columns:1fr}} .hero{{padding:30px}} .section{{padding:24px}}}}
</style>
</head>
<body><main class="shell">
<section class="hero"><p class="eyebrow">Hermes memory closeout · dry run</p><h1>Dream report with pattern-first staging.</h1><p class="lede">Read-only review of recent Hermes sessions, optional Linear completions, and optional merged GitHub PRs. Nothing was promoted to memory; one-off observations stage low, backend-aware routing separates compact standard memory, Hindsight/Obsidian context, and skill-worthy procedures.</p><div class="meta"><span class="pill">Window: {since}</span><span class="pill">Generated: {generated}</span><span class="pill">No durable writes</span><span class="pill">Pattern history gated</span></div></section>
<section class="section"><p class="eyebrow">Executive summary</p><h2>What the closeout layer saw.</h2><div class="metrics"><div class="metric"><strong>{summary['sessions_seen']}</strong><span>sessions</span></div><div class="metric"><strong>{summary['github_seen']}</strong><span>merged PRs</span></div><div class="metric"><strong>{summary['linear_seen']}</strong><span>completed Linear items</span></div><div class="metric"><strong>{summary['candidate_count']}</strong><span>candidate facts</span></div></div></section>
<section class="section"><p class="eyebrow">Diagram</p><h2>Collection → backend-aware staging → approved promotion.</h2><div class="diagram">{arch}</div></section>
<section class="section split"><div><p class="eyebrow">Routing breakdown</p><h2>Where candidates want to go.</h2><ul class="route-list">{route_rows}</ul></div><div><p class="eyebrow">Source health</p><h2>Dry-run coverage notes.</h2><ul class="notes">{source_notes_html}</ul></div></section>
<section class="section"><p class="eyebrow">Candidate board</p><h2>Top staged patterns.</h2><p class="lede">Candidates are intentionally conservative: single-night sightings should remain staged; distinct repeated evidence and source diversity raise confidence before recommending memory, Hindsight, Obsidian, or skill promotion. Re-running the script against the same evidence does not mature a pattern.</p><div class="candidate-grid">{top_candidates}</div></section>
<section class="section decision"><div class="box"><p class="eyebrow">Recommended next gate</p><h2>Let patterns mature before writes.</h2><p class="final-note">The dry run is useful as a signal-quality pass. The next version should keep dreaming nightly, maintain pattern history, and only surface candidates for approval after repeated observations create a stronger memory pattern.</p></div><div class="box"><p class="eyebrow">Artifacts</p><p class="final-note">Raw JSON companion: <code>{json_name}</code></p><p class="final-note">Command shape: <code>closeout_dream_report.py --since {since} --dry-run</code></p></div></section>
</main></body></html>"""


def main() -> int:
    args = parse_args()
    load_dotenv_keys()
    since_dt, since_label = parse_since(args.since)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    html_path = Path(args.output).expanduser() if args.output else OUTPUT_DIR / f"closeout-dream-report-{stamp}.html"
    json_path = Path(args.json_output).expanduser() if args.json_output else OUTPUT_DIR / f"closeout-dream-report-{stamp}.json"

    backend = detect_memory_backend()
    sessions = query_sessions(since_dt, args.max_sessions, args.max_messages_per_session)
    github = collect_github(since_dt)
    linear = collect_linear(since_dt)
    history = load_pattern_history()
    candidates = apply_pattern_history(extract_candidates(sessions, github, linear, backend), history, write_history=args.update_history)
    summary = summarize(sessions, github, linear, candidates, backend)
    report = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "since": since_label,
        "dry_run": True,
        "writes_performed": ["pattern_history"] if args.update_history else [],
        "backend": backend,
        "history_updated": bool(args.update_history),
        "sessions": sessions,
        "github": github,
        "linear": linear,
        "candidates": candidates,
        "summary": summary,
        "pattern_history_path": str(HISTORY_PATH),
        "json_path": str(json_path),
        "html_path": str(html_path),
    }
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    print(json.dumps({"html": str(html_path), "json": str(json_path), "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
