#!/usr/bin/env python3
"""Read-only exact-head snapshot for one GitHub pull request.

Compares the live PR head, its final commit, and the remote branch without
checking out or mutating the repository. Exit 0 means the requested live-state
conditions agree; exit 1 means they do not; command/config errors exit 2.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class SnapshotError(RuntimeError):
    pass


def run(argv: list[str], *, cwd: Path | None = None) -> str:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise SnapshotError(f"could not run {argv[0]}: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise SnapshotError(f"command failed ({completed.returncode}): {' '.join(argv)}: {detail}")
    return completed.stdout


def github_repo_from_remote(value: str) -> str | None:
    value = value.strip()
    patterns = (
        r"^git@github\.com:(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        r"^ssh://git@github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        r"^https?://github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$",
    )
    for pattern in patterns:
        match = re.match(pattern, value)
        if match:
            return match.group("repo")
    return None


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo", required=True, help="GitHub owner/name")
    result.add_argument("--pr", required=True, type=int, help="pull-request number")
    result.add_argument("--repo-path", required=True, type=Path, help="canonical local clone")
    result.add_argument("--expected-head", help="optional full SHA the caller expects")
    result.add_argument("--allow-draft", action="store_true")
    result.add_argument("--output", type=Path, help="optional JSON output path")
    return result


def main() -> int:
    args = parser().parse_args()
    repo_path = args.repo_path.expanduser().resolve()
    if not (repo_path / ".git").exists():
        raise SnapshotError(f"repo path is not a git worktree: {repo_path}")
    if args.pr < 1:
        raise SnapshotError("--pr must be a positive integer")
    if args.expected_head and not FULL_SHA.fullmatch(args.expected_head):
        raise SnapshotError("--expected-head must be a full lowercase 40-hex SHA")

    origin = run(["git", "remote", "get-url", "origin"], cwd=repo_path).strip()
    origin_repo = github_repo_from_remote(origin)

    fields = "number,url,state,isDraft,baseRefName,headRefName,headRefOid,commits"
    raw = run(
        ["gh", "pr", "view", str(args.pr), "--repo", args.repo, "--json", fields]
    )
    try:
        pr: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"gh returned invalid JSON: {exc}") from exc

    head = pr.get("headRefOid")
    branch = pr.get("headRefName")
    commits = pr.get("commits") or []
    final_commit = commits[-1].get("oid") if commits else None
    if not isinstance(head, str) or not FULL_SHA.fullmatch(head):
        raise SnapshotError("live PR has no valid full headRefOid")
    if not isinstance(branch, str) or not branch:
        raise SnapshotError("live PR has no head branch")

    remote_raw = run(
        ["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"],
        cwd=repo_path,
    ).strip()
    remote_head = remote_raw.split()[0] if remote_raw else None

    checks = {
        "origin_repo_matches": origin_repo == args.repo,
        "pr_is_open": pr.get("state") == "OPEN",
        "draft_allowed": bool(args.allow_draft or not pr.get("isDraft")),
        "pr_head_matches_final_commit": head == final_commit,
        "pr_head_matches_remote_branch": head == remote_head,
        "expected_head_matches": args.expected_head is None or head == args.expected_head,
    }
    ok = all(checks.values())
    result = {
        "schema_version": 1,
        "ok": ok,
        "repo": args.repo,
        "origin_url": origin,
        "origin_repo": origin_repo,
        "pr": pr.get("number"),
        "url": pr.get("url"),
        "state": pr.get("state"),
        "draft": pr.get("isDraft"),
        "base": pr.get("baseRefName"),
        "head_branch": branch,
        "head": head,
        "final_commit": final_commit,
        "remote_head": remote_head,
        "commit_count": len(commits),
        "checks": checks,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SnapshotError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
