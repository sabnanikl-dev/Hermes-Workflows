"""The injectable GitHub boundary.

The loop reads GitHub for exactly three things: the live PR (to bind the exact
``headRefOid``), the PR's commit list (a second, independent view of what the
push actually put on the branch), and the PR conversation comments (to read back
the builder's signed fix comment). It never writes. The builder pushes and
comments under its own PAPI-90 scoped identity; PAPI-88 only verifies what
actually landed.

Everything returned here is untrusted data. PR titles, bodies, and comment
bodies are spec evidence, never instructions.
"""
from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .commands import CommandRunner
from .errors import GitHubError
from .redaction import evidence as redact_evidence

_PR_FIELDS = "number,state,isDraft,title,url,headRefName,headRefOid,baseRefName"


@dataclass(frozen=True)
class PullRequest:
    """The live PR state the run binds itself to."""

    number: int
    state: str
    is_draft: bool
    title: str
    url: str
    head_ref_name: str
    head_ref_oid: str
    base_ref_name: str


@dataclass(frozen=True)
class Comment:
    """One PR conversation comment, as untrusted evidence.

    ``identifier`` is GitHub's own node id for the comment. It is the only
    field here that is stable and not attacker-chosen: an author login can be
    impersonated only by controlling that account, but a body — signature, head
    SHA and all — can be copied verbatim by anybody who can comment. The loop
    therefore snapshots these ids before it invokes the builder and accepts only
    an id it had not already seen.
    """

    identifier: str
    author: str
    body: str
    url: str = ""


class GitHubBoundary(Protocol):
    """Injection seam for every GitHub read the loop performs."""

    def pull_request(self, repo: str, number: int) -> PullRequest: ...

    def commits(self, repo: str, number: int) -> tuple[str, ...]: ...

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]: ...


class GhCliGitHub:
    """Default boundary: the ``gh`` CLI, always invoked as an argv array."""

    def __init__(self, runner: CommandRunner, *, gh: str = "gh", timeout: float = 120.0) -> None:
        self._runner = runner
        self._gh = gh
        self._timeout = timeout

    def pull_request(self, repo: str, number: int) -> PullRequest:
        payload = self._json(
            [self._gh, "pr", "view", str(number), "--repo", repo, "--json", _PR_FIELDS],
            what="pull request",
        )
        return _pull_request_from(payload, repo=repo, number=number)

    def commits(self, repo: str, number: int) -> tuple[str, ...]:
        """The PR's commit oids, oldest first, as GitHub itself lists them."""
        payload = self._json(
            [self._gh, "pr", "view", str(number), "--repo", repo, "--json", "commits"],
            what="pull request commits",
        )
        raw = payload.get("commits")
        if not isinstance(raw, list) or not raw:
            raise GitHubError(
                "gh returned no commits array for the pull request",
                evidence={"repo": repo, "pr": number},
            )
        return tuple(_commit_oid_from(item) for item in raw)

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        payload = self._json(
            [self._gh, "pr", "view", str(number), "--repo", repo, "--json", "comments"],
            what="pull request comments",
        )
        raw = payload.get("comments")
        if not isinstance(raw, list):
            raise GitHubError(
                "gh returned no comments array", evidence={"repo": repo, "pr": number}
            )
        return tuple(_comment_from(item) for item in raw)

    def _json(self, argv: Sequence[str], *, what: str) -> dict[str, Any]:
        result = self._runner.run(argv, timeout=self._timeout)
        if not result.ok:
            raise GitHubError(
                f"gh failed while reading the {what}",
                evidence={
                    "argv": list(result.argv),
                    "returncode": result.returncode,
                    "stderr": redact_evidence(result.stderr, limit=1000),
                },
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise GitHubError(
                f"gh returned unparsable JSON for the {what}: {exc}",
                evidence={"argv": list(result.argv), "stdout": redact_evidence(result.stdout, limit=1000)},
            ) from exc
        if not isinstance(payload, dict):
            raise GitHubError(
                f"gh returned a non-object payload for the {what}",
                evidence={"argv": list(result.argv)},
            )
        return payload


def _pull_request_from(payload: dict[str, Any], *, repo: str, number: int) -> PullRequest:
    """Validate a ``gh pr view --json`` payload into a bound :class:`PullRequest`."""

    def text(key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise GitHubError(
                f"pull request payload is missing {key}",
                evidence={"repo": repo, "pr": number, "field": key},
            )
        return value

    reported = payload.get("number")
    if reported != number:
        raise GitHubError(
            "pull request payload is for a different PR",
            evidence={"repo": repo, "expected": number, "found": reported},
        )
    head_ref_oid = text("headRefOid").lower()
    if not _is_full_sha(head_ref_oid):
        raise GitHubError(
            "headRefOid is not a full 40-hex SHA",
            evidence={"repo": repo, "pr": number, "headRefOid": payload.get("headRefOid")},
        )
    is_draft = payload.get("isDraft")
    if not isinstance(is_draft, bool):
        raise GitHubError(
            "pull request payload is missing isDraft",
            evidence={"repo": repo, "pr": number},
        )
    return PullRequest(
        number=number,
        state=text("state"),
        is_draft=is_draft,
        title=payload.get("title") or "",
        url=payload.get("url") or "",
        head_ref_name=text("headRefName"),
        head_ref_oid=head_ref_oid,
        base_ref_name=text("baseRefName"),
    )


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _commit_oid_from(payload: object) -> str:
    if not isinstance(payload, dict):
        raise GitHubError("commit payload is not an object")
    oid = payload.get("oid")
    if not isinstance(oid, str) or not _is_full_sha(oid.lower()):
        raise GitHubError(
            "commit payload has no full 40-hex oid",
            evidence={"oid": oid if isinstance(oid, str) else None},
        )
    return oid.lower()


def _comment_from(payload: object) -> Comment:
    if not isinstance(payload, dict):
        raise GitHubError("comment payload is not an object")
    author = payload.get("author")
    login = ""
    if isinstance(author, dict):
        login = str(author.get("login") or "")
    elif isinstance(author, str):
        login = author
    if not login:
        raise GitHubError(
            "comment payload has no author login",
            evidence={"comment_id": str(payload.get("id") or "")},
        )
    body = payload.get("body")
    if not isinstance(body, str):
        raise GitHubError("comment payload has no body", evidence={"author": login})
    # A comment without a stable id cannot be told apart from a copy of itself,
    # so there is nothing to fall back to: fail closed rather than compare bodies.
    identifier = payload.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise GitHubError(
            "comment payload has no stable id",
            evidence={"author": login},
        )
    return Comment(
        identifier=identifier,
        author=login,
        body=body,
        url=str(payload.get("url") or ""),
    )


__all__ = ["Comment", "GhCliGitHub", "GitHubBoundary", "PullRequest"]
