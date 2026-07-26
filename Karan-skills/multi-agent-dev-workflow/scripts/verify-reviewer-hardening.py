#!/usr/bin/env python3
"""Static verification for a least-privilege Hermes reviewer profile.

This checks durable configuration and launcher invariants. It does not replace
runtime negative tests for environment leakage, write blocking, or command-deny
rules.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: run with the Hermes Python environment") from exc


def parse_args() -> argparse.Namespace:
    home = Path.home()
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="reviewer")
    parser.add_argument("--hermes-root", type=Path, default=home / ".hermes")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--provider", default="openai-codex")
    parser.add_argument("--reasoning", default="medium")
    parser.add_argument(
        "--expected-skills",
        default="code-review,integration-audit-review,local-web-preview,web-application-qa",
    )
    parser.add_argument("--min-deny-rules", type=int, default=20)
    parser.add_argument("--reviewer-launcher", type=Path, default=home / ".local/bin/reviewer")
    parser.add_argument("--codex-launcher", type=Path, default=home / ".local/bin/codex-reviewer")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = args.hermes_root / "profiles" / args.profile
    expected_skills = sorted(x.strip() for x in args.expected_skills.split(",") if x.strip())
    errors: list[str] = []

    def check(value: object, message: str) -> None:
        if not value:
            errors.append(message)

    config_path = profile / "config.yaml"
    check(config_path.is_file(), f"missing config: {config_path}")
    if not config_path.is_file():
        return report(errors, {})

    config = yaml.safe_load(config_path.read_text()) or {}
    model = config.get("model", {})
    agent = config.get("agent", {})
    terminal = config.get("terminal", {})
    approvals = config.get("approvals", {})
    security = config.get("security", {})
    platform_toolsets = config.get("platform_toolsets", {})

    check(model.get("default") == args.model, "wrong reviewer model")
    check(model.get("provider") == args.provider, "wrong reviewer provider")
    check(agent.get("reasoning_effort") == args.reasoning, "wrong reasoning effort")
    check(terminal.get("home_mode") == "profile", "terminal.home_mode must be profile")
    check(terminal.get("env_passthrough") == [], "terminal.env_passthrough must be empty")
    check(terminal.get("auto_source_bashrc") is False, "shell startup sourcing must be disabled")
    check(terminal.get("persistent_shell") is False, "persistent shell must be disabled")
    check(config.get("command_allowlist") == [], "command allowlist must be empty")
    check(approvals.get("mode") in {"smart", "manual"}, "approval mode is unsafe")
    check(len(approvals.get("deny", [])) >= args.min_deny_rules, "deny-rule floor not met")
    check(security.get("redact_secrets") is True, "secret redaction must be enabled")
    check(security.get("tirith_fail_open") is False, "Tirith must fail closed")
    check(config.get("memory", {}).get("memory_enabled") is False, "memory must be disabled")
    check(config.get("memory", {}).get("user_profile_enabled") is False, "user profile injection must be disabled")
    check(config.get("curator", {}).get("enabled") is False, "curator must be disabled")
    check(config.get("checkpoints", {}).get("enabled") is False, "checkpoints must be disabled")
    check(config.get("delegation", {}).get("orchestrator_enabled") is False, "delegation orchestrator must be disabled")
    check("delegation" not in platform_toolsets.get("cli", []), "delegation toolset must not be enabled")
    check("memory" not in platform_toolsets.get("cli", []), "memory toolset must not be enabled")
    for platform in ("telegram", "discord", "whatsapp", "slack", "signal", "homeassistant"):
        check(platform_toolsets.get(platform) == [], f"{platform} toolsets must be empty")

    skills_dir = profile / "skills"
    skills = sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")) if skills_dir.is_dir() else []
    check(skills == expected_skills, f"skill allowlist mismatch: {skills}")
    check((profile / ".no-bundled-skills").is_file(), "missing .no-bundled-skills")

    env_path = profile / ".env"
    allowed_policy_env = {"HERMES_WRITE_SAFE_ROOT", "HERMES_REDACT_SECRETS", "HERMES_YOLO_MODE"}
    env_keys: set[str] = set()
    if env_path.is_file():
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                env_keys.add(line.split("=", 1)[0])
    check(env_keys <= allowed_policy_env, f"unexpected profile env keys: {sorted(env_keys - allowed_policy_env)}")
    if env_path.exists():
        check(stat.S_IMODE(env_path.stat().st_mode) == 0o600, ".env permissions must be 0600")
    auth_path = profile / "auth.json"
    if auth_path.exists():
        check(stat.S_IMODE(auth_path.stat().st_mode) == 0o600, "auth.json permissions must be 0600")

    for name, launcher in (("reviewer", args.reviewer_launcher), ("codex-reviewer", args.codex_launcher)):
        check(launcher.is_file(), f"missing launcher: {launcher}")
        if not launcher.is_file():
            continue
        text = launcher.read_text()
        check("/usr/bin/env -i" in text, f"{name} lacks clean-environment launch")
        check("GH_TOKEN" not in text, f"{name} must not pass GH_TOKEN to reviewer children")
        check(stat.S_IMODE(launcher.stat().st_mode) == 0o700, f"{name} permissions must be 0700")
    if args.reviewer_launcher.is_file():
        text = args.reviewer_launcher.read_text()
        check("HERMES_WRITE_SAFE_ROOT=/tmp" in text, "reviewer launcher lacks /tmp write sandbox")
        check("--yolo" in text and "blocked override" in text, "reviewer launcher lacks override rejection")
    if args.codex_launcher.is_file():
        text = args.codex_launcher.read_text()
        check("--sandbox \"$sandbox\"" in text, "Codex launcher lacks sandbox pin")
        check("gpt-5.6-sol" in text and "medium" in text, "Codex launcher lacks runtime pin")

    snapshot = profile / ".skills_prompt_snapshot.json"
    if snapshot.is_file():
        snapshot_text = snapshot.read_text()
        for skill in expected_skills:
            check(skill in snapshot_text, f"skill snapshot missing {skill}")

    summary = {
        "profile": args.profile,
        "model": model.get("default"),
        "provider": model.get("provider"),
        "reasoning": agent.get("reasoning_effort"),
        "skills": skills,
        "deny_rules": len(approvals.get("deny", [])),
        "errors": errors,
    }
    return report(errors, summary)


def report(errors: list[str], summary: dict) -> int:
    print(json.dumps(summary, indent=2, sort_keys=True))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("REVIEWER_STATIC_HARDENING_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
