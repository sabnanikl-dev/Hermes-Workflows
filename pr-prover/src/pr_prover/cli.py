"""Command line entry point.

    pr-prover run --config <run.json> [--json]
    pr-prover check-config --config <run.json>
    pr-prover reset --config <run.json>

Exit codes are the outcome::

    0  merge-ready   1  blocked   2  needs-karan (including every fail-closed stop)
    64 usage or configuration error
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .commands import SubprocessRunner
from .config import RunConfig
from .errors import PrProverError
from .github import GhCliGitHub
from .loop import NEEDS_KARAN, ProverLoop
from .report import to_json, to_markdown
from .worktrees import SourceRepo, WorktreeProvider

USAGE_ERROR = 64


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-prover",
        description="Prove an existing pull request merge-ready, blocked, or needing Karan.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run the prove loop for one PR")
    run.add_argument("--config", required=True, type=Path, help="path to the run config JSON")
    run.add_argument("--json", action="store_true", help="emit the machine-readable report")

    check = subparsers.add_parser("check-config", help="validate a run config and exit")
    check.add_argument("--config", required=True, type=Path)

    reset = subparsers.add_parser(
        "reset", help="delete the local state file for a finished or abandoned run"
    )
    reset.add_argument("--config", required=True, type=Path)
    reset.add_argument(
        "--force", action="store_true", help="also remove a stale lockfile (confirm no run is active)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = RunConfig.load(args.config)
    except PrProverError as exc:
        print(f"pr-prover: {exc.reason}: {exc.message}", file=sys.stderr)
        return USAGE_ERROR

    if args.command == "check-config":
        print(
            f"config ok: {config.repo}#{config.pr} "
            f"({len(config.gates)} gate(s), {len(config.reviewers)} reviewer lane(s))"
        )
        for reviewer in config.reviewers:
            how = (
                f"relays as {reviewer.artifact_author} via {reviewer.relay.argv[0]}"
                if reviewer.relay is not None
                else f"publishes as {reviewer.artifact_author}"
            )
            print(f"  reviewer {reviewer.name}: role {reviewer.role}, {how}")
        print(f"  builder: comments as {config.builder.comment_author}")
        for note in config.advisories():
            print(f"  advisory: {note}")
        return 0

    if args.command == "reset":
        return _reset(config, force=args.force)

    try:
        runner = SubprocessRunner()
        source = SourceRepo(runner=runner, path=config.source_repo)
        loop = ProverLoop(
            config,
            runner=runner,
            github=GhCliGitHub(runner),
            worktrees=WorktreeProvider(source, config.worktree_root),
        )
    except PrProverError as exc:
        print(f"pr-prover: {exc.reason}: {exc.message}", file=sys.stderr)
        return USAGE_ERROR

    result = loop.run()
    print(to_json(result) if args.json else to_markdown(result), end="")
    if result.outcome == NEEDS_KARAN:
        print(f"pr-prover: stopped and asking Karan ({result.reason})", file=sys.stderr)
    return result.exit_code


def _reset(config: RunConfig, *, force: bool) -> int:
    removed: list[str] = []
    if config.state_file.exists():
        config.state_file.unlink()
        removed.append(str(config.state_file))
    if force and config.lock_file.exists():
        config.lock_file.unlink()
        removed.append(str(config.lock_file))
    elif config.lock_file.exists():
        print(
            f"pr-prover: lockfile {config.lock_file} still exists; "
            "confirm no run is active, then re-run with --force",
            file=sys.stderr,
        )
        return USAGE_ERROR
    print("removed: " + (", ".join(removed) if removed else "nothing"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
