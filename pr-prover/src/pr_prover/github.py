"""The injectable GitHub boundary.

The loop reads GitHub for exactly three things: the live PR (to bind the exact
``headRefOid``), the PR conversation comments (to read back the builder's signed
fix comment), and the PR reviews (to read back each reviewer lane's artifact
under its own identity). It never writes. Children push, comment, and review
under their own scoped identities; the loop only verifies what actually landed.

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


@dataclass(frozen=True)
class Review:
    """One submitted review, as untrusted evidence.

    ``commit_oid`` is the part that matters to this loop: GitHub records which
    commit a review was submitted against, so a review artifact can be bound to
    the exact head it reviewed rather than to whatever the PR points at now.
    """

    identifier: str
    author: str
    body: str
    commit_oid: str
    state: str = ""
    url: str = ""


class GitHubBoundary(Protocol):
    """Injection seam for every GitHub read the loop performs."""

    def pull_request(self, repo: str, number: int) -> PullRequest: ...

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]: ...

    def reviews(self, repo: str, number: int) -> tuple[Review, ...]: ...


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

    def reviews(self, repo: str, number: int) -> tuple[Review, ...]:
        """Read submitted reviews, each with the commit it was submitted against.

        ``gh pr view --json reviews`` does not carry the reviewed commit, so this
        goes to the REST endpoint that does: without it a review artifact could
        only ever be bound to a login, not to a head.
        """
        payload = self._call(
            [
                self._gh,
                "api",
                f"repos/{repo}/pulls/{number}/reviews?per_page=100",
                "--header",
                "Accept: application/vnd.github+json",
            ],
            what="pull request reviews",
        )
        if not isinstance(payload, list):
            raise GitHubError(
                "gh returned no reviews array", evidence={"repo": repo, "pr": number}
            )
        return tuple(_review_from(item) for item in payload)

    def _json(self, argv: Sequence[str], *, what: str) -> dict[str, Any]:
        payload = self._call(argv, what=what)
        if not isinstance(payload, dict):
            raise GitHubError(
                f"gh returned a non-object payload for the {what}",
                evidence={"argv": list(argv)},
            )
        return payload

    def _call(self, argv: Sequence[str], *, what: str) -> Any:
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
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise GitHubError(
                f"gh returned unparsable JSON for the {what}: {exc}",
                evidence={"argv": list(result.argv), "stdout": redact_evidence(result.stdout, limit=1000)},
            ) from exc


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
    if len(head_ref_oid) != 40 or any(character not in "0123456789abcdef" for character in head_ref_oid):
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


def _review_from(payload: object) -> Review:
    if not isinstance(payload, dict):
        raise GitHubError("review payload is not an object")
    user = payload.get("user")
    login = str(user.get("login") or "") if isinstance(user, dict) else ""
    if not login:
        raise GitHubError(
            "review payload has no author login",
            evidence={"review_id": str(payload.get("id") or "")},
        )
    identifier = payload.get("id")
    if not isinstance(identifier, (str, int)) or isinstance(identifier, bool) or str(identifier) == "":
        raise GitHubError("review payload has no stable id", evidence={"author": login})
    commit_oid = str(payload.get("commit_id") or "").lower()
    if len(commit_oid) != 40 or any(character not in "0123456789abcdef" for character in commit_oid):
        raise GitHubError(
            "review payload does not name the exact commit it reviewed",
            evidence={"author": login, "commit_id": str(payload.get("commit_id") or "")},
        )
    body = payload.get("body")
    return Review(
        identifier=str(identifier),
        author=login,
        body=body if isinstance(body, str) else "",
        commit_oid=commit_oid,
        state=str(payload.get("state") or ""),
        url=str(payload.get("html_url") or ""),
    )


__all__ = ["Comment", "GhCliGitHub", "GitHubBoundary", "PullRequest", "Review"]
