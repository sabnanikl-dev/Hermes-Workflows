#!/usr/bin/env python3
"""Deterministically relay a prepared Integration Auditor artifact to a PR comment.

The reviewer model never receives GitHub credentials. This sidecar verifies the
exact live PR head, reviewer identity, canonical artifact markers, duplicate
state, and byte-for-byte remote readback.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run_json(args, env, payload=None):
    cmd = ["gh", "api", *args]
    if payload:
        cmd.extend(["--input", payload])
    proc = subprocess.run(cmd, env=env, text=True, capture_output=True, check=True)
    return json.loads(proc.stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, help="owner/repo")
    p.add_argument("--pr", type=int, required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--artifact", required=True)
    p.add_argument("--status", choices=("pass", "fail", "needs-human"), required=True)
    p.add_argument("--blocking", type=int, required=True)
    p.add_argument("--reviewer", default="karanagent1")
    p.add_argument("--publish", action="store_true")
    args = p.parse_args()

    body = Path(args.artifact).read_text(encoding="utf-8")
    required = (
        "Reviewed by: Hermes Integration Auditor profile",
        f"PR: #{args.pr} | Head: {args.head}",
        f"DONE: REVIEWER=INTEGRATION_AUDITOR STATUS={args.status} "
        f"BLOCKING={args.blocking} HEAD={args.head} ARTIFACT=relay-required",
    )
    if not body or any(body.count(marker) != 1 for marker in required):
        raise SystemExit("integration artifact canonical shape mismatch")

    base_env = os.environ.copy()
    base_env.pop("GH_TOKEN", None)
    base_env.pop("GITHUB_TOKEN", None)
    token = subprocess.run(
        ["gh", "auth", "token", "--hostname", "github.com", "--user", args.reviewer],
        env=base_env,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    env = base_env | {"GH_TOKEN": token}

    if run_json(["user"], env).get("login") != args.reviewer:
        raise SystemExit("reviewer identity mismatch")
    if run_json([f"repos/{args.repo}/pulls/{args.pr}"], env).get("head", {}).get("sha") != args.head:
        raise SystemExit("live PR head mismatch")

    comments = run_json([f"repos/{args.repo}/issues/{args.pr}/comments?per_page=100"], env)
    for item in comments:
        if item.get("body") == body:
            print(json.dumps({"status": "already-published", "id": item.get("id"), "url": item.get("html_url")}))
            return

    if not args.publish:
        print(json.dumps({"status": "ready", "reviewer": args.reviewer, "head": args.head}))
        return

    payload_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump({"body": body}, handle, ensure_ascii=False)
            handle.write("\n")
            payload_path = handle.name
        created = run_json(["--method", "POST", f"repos/{args.repo}/issues/{args.pr}/comments"], env, payload_path)
        comment_id = created.get("id")
        readback = run_json([f"repos/{args.repo}/issues/comments/{comment_id}"], env)
        if readback.get("user", {}).get("login") != args.reviewer or readback.get("body") != body:
            raise SystemExit("integration artifact readback mismatch")
        if run_json([f"repos/{args.repo}/pulls/{args.pr}"], env).get("head", {}).get("sha") != args.head:
            raise SystemExit("PR head drifted during publication")
        print(json.dumps({
            "status": "published-and-verified",
            "id": comment_id,
            "url": readback.get("html_url"),
            "head": args.head,
        }, sort_keys=True))
    finally:
        if payload_path:
            Path(payload_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
