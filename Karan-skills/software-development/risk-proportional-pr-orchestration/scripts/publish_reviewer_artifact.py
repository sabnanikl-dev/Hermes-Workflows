#!/usr/bin/env python3
"""Publish one exact Codex reviewer artifact under a dedicated GitHub identity.

The model never receives the token. This deterministic sidecar resolves the
reviewer credential after model exit, verifies the live head and artifact, posts
only with --publish, and reads the immutable artifact back byte-for-byte.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_ARTIFACT_BYTES = 128 * 1024


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--pr", required=True, type=int)
    p.add_argument("--head", required=True)
    p.add_argument("--role", required=True, choices=("A", "B"))
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--reviewer-login", default="karanagent1")
    p.add_argument("--publish", action="store_true", help="perform the external POST")
    return p


def gh(args: list[str], *, env: dict[str, str], payload: Path | None = None) -> object:
    command = ["gh", "api", *args]
    if payload is not None:
        command += ["--input", str(payload)]
    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"GitHub API call failed for {args[-1]!r}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def temporary_payload(value: object) -> Path:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    try:
        json.dump(value, handle, ensure_ascii=False)
        handle.write("\n")
        return Path(handle.name)
    finally:
        handle.close()


def validate_artifact(path: Path, *, role: str, head: str) -> str:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("artifact must be one regular non-symlink file")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise RuntimeError("artifact is empty or exceeds the bounded size")
    body = raw.decode("utf-8")
    lines = body.splitlines()
    # Markdown-producing reviewers may leave harmless trailing spaces on declaration
    # lines. Normalize only for shape validation; publish/read back the original body
    # bytes unchanged so the sidecar still transports the model's exact artifact.
    declaration_lines = [line.rstrip() for line in lines]
    role_lines = [line for line in declaration_lines if line in (f"REVIEWER: {role}", f"ROLE=reviewer-{role.lower()}")]
    head_lines = [line for line in declaration_lines if line in (f"HEAD: {head}", f"HEAD={head}")]
    status_lines = [line for line in declaration_lines if line.startswith("STATUS:") or line.startswith("STATUS=")]
    blocker_lines = [line for line in declaration_lines if line.startswith("BLOCKERS:") or line.startswith("BLOCKING=")]
    if len(role_lines) != 1 or len(head_lines) != 1:
        raise RuntimeError("artifact must contain exactly one canonical role and exact-head declaration")
    if len(status_lines) != 1 or len(blocker_lines) != 1:
        raise RuntimeError("artifact must contain exactly one status and blocker-count declaration")
    return body


def main() -> None:
    args = parser().parse_args()
    if not FULL_SHA.fullmatch(args.head):
        raise SystemExit("--head must be a full lowercase 40-hex SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        raise SystemExit("--repo must be owner/name")

    body = validate_artifact(args.artifact, role=args.role, head=args.head)
    base_env = os.environ.copy()
    base_env.pop("GH_TOKEN", None)
    base_env.pop("GITHUB_TOKEN", None)
    token = subprocess.run(
        ["gh", "auth", "token", "--hostname", "github.com", "--user", args.reviewer_login],
        env=base_env,
        text=True,
        capture_output=True,
        check=False,
    )
    if token.returncode != 0 or not token.stdout.strip():
        raise SystemExit("dedicated reviewer credential could not be resolved")
    reviewer_env = base_env | {"GH_TOKEN": token.stdout.strip()}

    identity = gh(["user"], env=reviewer_env)
    if not isinstance(identity, dict) or identity.get("login") != args.reviewer_login:
        raise SystemExit("dedicated reviewer identity verification failed")
    pull = gh([f"repos/{args.repo}/pulls/{args.pr}"], env=reviewer_env)
    if not isinstance(pull, dict) or pull.get("head", {}).get("sha") != args.head:
        raise SystemExit("live PR head does not equal the reviewed head")

    if args.role == "A":
        collection = gh([f"repos/{args.repo}/pulls/{args.pr}/reviews?per_page=100"], env=reviewer_env)
    else:
        collection = gh([f"repos/{args.repo}/issues/{args.pr}/comments?per_page=100"], env=reviewer_env)
    if not isinstance(collection, list):
        raise SystemExit("GitHub artifact inventory was not a list")
    duplicates = [item for item in collection if item.get("body") == body]
    if duplicates:
        print(json.dumps({"status": "already-published", "role": args.role, "id": duplicates[0].get("id")}))
        return

    if not args.publish:
        print(json.dumps({"status": "ready", "role": args.role, "head": args.head, "reviewer": args.reviewer_login}))
        return

    payload: Path | None = None
    try:
        if args.role == "A":
            status = next(line for line in body.splitlines() if line.startswith("STATUS:") or line.startswith("STATUS="))
            blocked = "block" in status.lower() or "fail" in status.lower()
            event = "REQUEST_CHANGES" if blocked else "APPROVE"
            payload = temporary_payload({"body": body, "event": event, "commit_id": args.head})
            created = gh(["--method", "POST", f"repos/{args.repo}/pulls/{args.pr}/reviews"], env=reviewer_env, payload=payload)
            artifact_id = created.get("id") if isinstance(created, dict) else None
            if not artifact_id:
                raise RuntimeError("formal review POST returned no immutable ID")
            readback = gh([f"repos/{args.repo}/pulls/{args.pr}/reviews/{artifact_id}"], env=reviewer_env)
            if readback.get("commit_id") != args.head:
                raise RuntimeError("formal review readback head mismatch")
            url = readback.get("html_url")
        else:
            payload = temporary_payload({"body": body})
            created = gh(["--method", "POST", f"repos/{args.repo}/issues/{args.pr}/comments"], env=reviewer_env, payload=payload)
            artifact_id = created.get("id") if isinstance(created, dict) else None
            if not artifact_id:
                raise RuntimeError("review comment POST returned no immutable ID")
            readback = gh([f"repos/{args.repo}/issues/comments/{artifact_id}"], env=reviewer_env)
            url = readback.get("html_url")

        if readback.get("user", {}).get("login") != args.reviewer_login:
            raise RuntimeError("immutable readback author mismatch")
        if readback.get("body") != body:
            raise RuntimeError("immutable readback body mismatch")
        final_pull = gh([f"repos/{args.repo}/pulls/{args.pr}"], env=reviewer_env)
        if final_pull.get("head", {}).get("sha") != args.head:
            raise RuntimeError("live PR head drifted during publication")
        print(json.dumps({"status": "published-and-verified", "role": args.role, "id": artifact_id, "url": url, "head": args.head, "reviewer": args.reviewer_login}, sort_keys=True))
    finally:
        if payload is not None:
            try:
                payload.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    main()
