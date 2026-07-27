"""Command line entry point.

    pr-prover run --config <run.json> [--json]
    pr-prover check-config --config <run.json>
    pr-prover reset --config <run.json>

Exit codes are the outcome::

    0  merge-ready   1  blocked   2  needs-karan (including every fail-closed stop)
    64 usage or configuration error

A run that never reaches a loop still reaches the same structured failure. An
unusable config or an unbuildable child-command template stops before a
:class:`~pr_prover.loop.RunResult` exists, but ``invalid-config`` and
``invalid-command`` are declared failure classes with playbooks, so they are
rendered from a :class:`~pr_prover.errors.FailureRecord` here exactly as the
loop's own stops are — the same four answers, in the same two renderings — and
not as one line of prose the builder cannot act on.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .commands import SubprocessRunner
from .config import RunConfig
from .errors import FailureRecord, PrProverError
from .github import GhCliGitHub
from .loop import NEEDS_KARAN, ProverLoop
from .redaction import sanitize
from .report import failure_markdown, to_json, to_markdown
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
    as_json = bool(getattr(args, "json", False))
    try:
        config = RunConfig.load(args.config)
    except PrProverError as exc:
        return _fail_closed(exc, as_json=as_json)

    if args.command == "check-config":
        print(
            f"config ok: {config.repo}#{config.pr} "
            f"({len(config.gates)} gate(s), {len(config.reviewers)} reviewer lane(s): "
            + ", ".join(reviewer.role for reviewer in config.reviewers)
            + "; governed by "
            + ", ".join(f"#{number}" for number in config.governing_issues)
            + ")"
        )
        # Advisories are notes, not errors: a lane budget that is unrealistically
        # short or absent produces a run that looks like a hang or never ends,
        # and neither is something to discover for the first time at minute
        # forty of a real fix cycle. They are printed rather than enforced
        # because a repository with a two-minute suite may genuinely know better.
        for note in config.advisories():
            print(f"note: {note}")
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
        return _fail_closed(exc, as_json=as_json)

    result = loop.run()
    print(to_json(result) if args.json else to_markdown(result), end="")
    if result.outcome == NEEDS_KARAN:
        print(f"pr-prover: stopped and asking Karan ({result.reason})", file=sys.stderr)
    return result.exit_code


def _fail_closed(exc: PrProverError, *, as_json: bool) -> int:
    """Report a stop that happened before the loop existed, in the shipped shape.

    The record is sanitized here for the same reason the report is: this is the
    last place a config path, a template, or a captured message can reach a
    terminal. The prose line on stderr stays, because it is what an operator
    reads in a log, but it is now a summary of the record on stdout rather than
    the only thing the failure produced.

    That summary is read back out of the sanitized record rather than off the
    exception, because stderr is a terminal too. Printing ``exc.message`` beside
    a scrubbed stdout put the same failure through the redaction boundary twice
    with two different answers, and the unscrubbed one — a credential-shaped
    config path, a template carrying a token — is the one that reaches an
    operator's log and CI capture. One sanitized record now feeds all three
    channels, so JSON, Markdown, and the stderr line cannot disagree about what
    is safe to print.

    The heading says the run never started rather than naming a run outcome:
    this returns the usage exit code, and a report that printed an outcome word
    over a different exit code would be claiming a run happened.
    """
    record = sanitize(FailureRecord.from_error(exc).as_dict())
    if as_json:
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        lines = [
            "## pr-prover — stopped before the run started",
            "",
            "### What failed and what to do next",
        ]
        lines += failure_markdown(record)
        print("\n".join(lines))
    print(
        f"pr-prover: {record['failure_class']}: {record['what_failed']}",
        file=sys.stderr,
    )
    return USAGE_ERROR


def _reset(config: RunConfig, *, force: bool) -> int:
    """Delete this run's control files, or refuse before deleting anything.

    The refusal is decided first, on purpose. A held lock means a run may still
    be in flight, and its state file is the only record of which attempt it is
    on and what verification it owes — so a reset that refuses must leave both
    files exactly as it found them rather than removing the journal on its way
    to returning an error.
    """
    if config.lock_file.exists() and not force:
        print(
            f"pr-prover: lockfile {config.lock_file} still exists; "
            "confirm no run is active, then re-run with --force. "
            "Nothing was removed.",
            file=sys.stderr,
        )
        return USAGE_ERROR
    removed: list[str] = []
    if config.state_file.exists():
        config.state_file.unlink()
        removed.append(str(config.state_file))
    if force and config.lock_file.exists():
        config.lock_file.unlink()
        removed.append(str(config.lock_file))
    print("removed: " + (", ".join(removed) if removed else "nothing"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
