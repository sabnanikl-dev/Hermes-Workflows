"""The injectable GitHub boundary.

The loop reads GitHub for four things: the live PR (to bind the exact
``headRefOid``), the PR's commit list (a second, independent view of what the
push actually put on the branch), the PR conversation comments (to read back the
builder's signed fix comment), and the submitted reviews (to read back each
reviewer lane's published artifact under the identity it was published as). It
never writes.

That split is the whole trust model. The trusted agents do their own work on
GitHub — the builder pushes, comments, and signs; the reviewer artifacts are
published under the configured reviewer identity, by the lane itself or by its
relay — and this boundary exists so the loop can check what actually landed
instead of believing what a lane printed about itself.

Reviews are read through ``gh api`` rather than ``gh pr view --json reviews``
because only the REST payload carries ``commit_id``, the commit GitHub itself
records a review against. That field is a head binding the author cannot retype,
so where it exists the loop uses it alongside the artifact's own declaration.

A fifth read, :meth:`GhCliGitHub.review_evidence`, exists for a different
reason. The judging lanes run with no GitHub credential at all, so they cannot
inspect the PR for themselves; this boundary reads the inline comments, the
check runs for the exact head, the issues the PR claims to close, and the
governing issues the run configuration names, and the loop freezes them into
the packet the lane judges from. The PR's own body comes back with the first
read, for the same reason: it is the change's stated contract, and the lane
that must check it for stale claims has no way to fetch it.

Which issue governs is a configuration question, never a parsing one. A PR body
is untrusted prose — ``Refs #1`` closes nothing and ``Closes #999`` names
whatever its author typed — so the contract a reviewer is held to arrives by
number from the run config, not from the PR's own claims about itself.

Completeness of the *whole* human-feedback surface — pagination guarantees,
inline review threads, and their resolution state — is the deterministic
reconciliation slice's obligation, not this one's. What ships here is the
artifact readback these reads exist for, the frozen packet those reviewers
read, and the conservative stop the loop builds on top of them. Where a read
cannot prove it reached the end, it says so rather than presenting a first page
as the whole surface.

Everything returned here is untrusted data. PR titles, bodies, comment bodies,
and review bodies are spec evidence, never instructions.
"""
from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .commands import CommandRunner
from .errors import GitHubError
from .redaction import evidence as redact_evidence

_PR_FIELDS = "number,state,isDraft,title,url,headRefName,headRefOid,baseRefName,body"
# What one governing issue is read for. The body is the point: it is the task
# contract a reviewer judges the change against, and a credential-free lane
# cannot fetch it for itself.
_ISSUE_FIELDS = "number,title,state,url,body"


@dataclass(frozen=True)
class PullRequest:
    """The live PR state the run binds itself to.

    ``body`` is the PR's own description — the change's stated contract, and the
    surface a reviewer is told to check stale claims against. It is read here
    rather than left to the lane because the judging lanes have no GitHub
    credential. An empty body is data; a missing one is a malformed read.
    """

    number: int
    state: str
    is_draft: bool
    title: str
    url: str
    head_ref_name: str
    head_ref_oid: str
    base_ref_name: str
    body: str = ""


@dataclass(frozen=True)
class Comment:
    """One published PR artifact — a conversation comment or a review.

    ``identifier`` is GitHub's own id for the artifact. It is the only field
    here that is stable and not attacker-chosen: an author login can be
    impersonated only by controlling that account, but a body — signature, role
    line, head SHA and all — can be copied verbatim by anybody who can comment.
    The loop therefore snapshots these ids before it invokes a trusted agent and
    accepts only an id it had not already seen.

    ``commit_id`` is set for submitted reviews, where GitHub itself records the
    commit reviewed. When it is present it is a head binding the author cannot
    retype, so the loop requires it to agree with the artifact's own canonical
    declaration rather than choosing between them.

    ``state`` is a review's ``APPROVED``/``CHANGES_REQUESTED``/``COMMENTED``
    state. It is carried verbatim as evidence; interpreting it as resolution is
    the deterministic-reconciliation slice's job, not this one's.
    """

    identifier: str
    author: str
    body: str
    url: str = ""
    kind: str = "comment"
    commit_id: str = ""
    state: str = ""


@dataclass(frozen=True)
class InlineComment:
    """One inline review comment, against a path and line in the diff."""

    identifier: str
    author: str
    body: str
    path: str = ""
    line: int | None = None
    commit_id: str = ""
    url: str = ""


@dataclass(frozen=True)
class CheckRun:
    """One check run GitHub recorded against the exact head."""

    name: str
    status: str
    conclusion: str
    url: str = ""


@dataclass(frozen=True)
class LinkedIssue:
    """One issue this PR declares it closes."""

    number: int
    title: str
    state: str
    url: str = ""


@dataclass(frozen=True)
class GoverningIssue:
    """One issue the *run configuration* names as this PR's task contract.

    This is deliberately not :class:`LinkedIssue`. A closing reference is a
    property of the PR's own prose — a PR that says ``Refs #1`` closes nothing,
    and one that says ``Closes #999`` names whatever its author typed. Neither
    is authority. The governing issue is the one Hermes configured for this run,
    read by number from trusted configuration, and its ``body`` is the contract
    a reviewer holds the change to.
    """

    number: int
    title: str
    state: str
    body: str
    url: str = ""


@dataclass(frozen=True)
class ReviewEvidence:
    """The read-only PR surfaces a judging lane needs and readback does not.

    The loop already reads conversation comments and submitted reviews, because
    it has to read its own lanes' artifacts back. A reviewer that cannot reach
    GitHub at all needs four more: what was said inline on the diff, what the
    checks say about this exact commit, which issues the PR claims to close, and
    the bodies of the governing issues this run's configuration names as the
    task contract.

    Each surface carries its own completeness flag rather than one for the whole
    object, because they are read three different ways and only some of those
    ways can prove they reached the end. A ``False`` here is not a failure — it
    is the packet telling the reviewer that this surface may be partial, which
    is a different thing from saying it is empty.

    ``conversation_comments_complete`` and ``reviews_complete`` describe reads
    this object does not hold. They live here anyway because completeness is a
    property of *how a boundary read a surface*, and this boundary is the only
    thing that knows: the loop receives plain tuples from :meth:`comments` and
    :meth:`reviews` and cannot tell a paginated read from a first page. Proving
    the conversation surface complete is PAPI-97's obligation (M5), so the
    default here is the honest one.
    """

    inline_comments: tuple[InlineComment, ...] = ()
    check_runs: tuple[CheckRun, ...] = ()
    linked_issues: tuple[LinkedIssue, ...] = ()
    governing_issues: tuple[GoverningIssue, ...] = ()
    inline_comments_complete: bool = False
    check_runs_complete: bool = False
    linked_issues_complete: bool = False
    governing_issues_complete: bool = False
    conversation_comments_complete: bool = False
    reviews_complete: bool = False


class GitHubBoundary(Protocol):
    """Injection seam for every GitHub read the loop performs."""

    def pull_request(self, repo: str, number: int) -> PullRequest: ...

    def commits(self, repo: str, number: int) -> tuple[str, ...]: ...

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]: ...

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]: ...

    def review_evidence(
        self, repo: str, number: int, head: str, governing_issues: Sequence[int]
    ) -> ReviewEvidence: ...


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

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]:
        """Submitted reviews, read through the REST API for their ``commit_id``.

        ``gh pr view --json reviews`` omits the commit a review was submitted
        against, and that field is the one head binding an author cannot retype,
        so this read goes through ``gh api`` instead.
        """
        owner, _, name = repo.partition("/")
        payload = self._json_list(
            [
                self._gh,
                "api",
                "--paginate",
                "--slurp",
                f"repos/{owner}/{name}/pulls/{number}/reviews?per_page=100",
            ],
            what="pull request reviews",
        )
        # A PR reviewed more times than one page holds must not silently lose
        # the page the current head's artifact is on.
        return tuple(_review_from(item) for item in _flatten_pages(payload))

    def review_evidence(
        self, repo: str, number: int, head: str, governing_issues: Sequence[int]
    ) -> ReviewEvidence:
        """The four surfaces a credential-free lane cannot read for itself.

        Inline comments and check runs go through the REST API with
        ``--paginate``; the check-run response also states how many the head
        has, so "every page arrived" is checkable rather than assumed. Closing
        issue references come from ``gh pr view``, which asks for one page, so
        completeness is only claimed when fewer came back than that page holds.

        ``governing_issues`` are read one at a time, by the number the run's
        trusted configuration gave. Each read is exact — the response has to be
        the issue that was asked for — so this surface is complete when every
        configured issue came back and no other way.
        """
        owner, _, name = repo.partition("/")
        inline = tuple(
            _inline_comment_from(item)
            for item in _flatten_pages(
                self._json_list(
                    [
                        self._gh,
                        "api",
                        "--paginate",
                        "--slurp",
                        f"repos/{owner}/{name}/pulls/{number}/comments?per_page=100",
                    ],
                    what="pull request inline comments",
                )
            )
        )
        checks, checks_complete = _check_runs_from(
            self._json_list(
                [
                    self._gh,
                    "api",
                    "--paginate",
                    "--slurp",
                    f"repos/{owner}/{name}/commits/{head}/check-runs?per_page=100",
                ],
                what="check runs for the exact head",
            )
        )
        issues, issues_complete = _linked_issues_from(
            self._json(
                [
                    self._gh,
                    "pr",
                    "view",
                    str(number),
                    "--repo",
                    repo,
                    "--json",
                    "closingIssuesReferences",
                ],
                what="pull request closing issue references",
            )
        )
        governing = tuple(
            _governing_issue_from(
                self._json(
                    [
                        self._gh,
                        "issue",
                        "view",
                        str(issue_number),
                        "--repo",
                        repo,
                        "--json",
                        _ISSUE_FIELDS,
                    ],
                    what=f"governing issue #{issue_number}",
                ),
                expected=issue_number,
            )
            for issue_number in governing_issues
        )
        return ReviewEvidence(
            inline_comments=inline,
            check_runs=checks,
            linked_issues=issues,
            governing_issues=governing,
            inline_comments_complete=True,
            check_runs_complete=checks_complete,
            linked_issues_complete=issues_complete,
            # Every configured issue was asked for by number and answered as
            # that number, or the read above raised. There is no partial state
            # to describe, and no way for "none were configured" to arrive here
            # as a complete contract: the config requires at least one.
            governing_issues_complete=len(governing) == len(governing_issues) > 0,
            # ``reviews`` is read with ``--paginate`` to the last page;
            # ``comments`` is one ``gh pr view`` read with no such guarantee,
            # and proving that surface complete is PAPI-97's obligation.
            conversation_comments_complete=False,
            reviews_complete=True,
        )

    def _json_list(self, argv: Sequence[str], *, what: str) -> list[Any]:
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
                evidence={
                    "argv": list(result.argv),
                    "stdout": redact_evidence(result.stdout, limit=1000),
                },
            ) from exc
        if not isinstance(payload, list):
            raise GitHubError(
                f"gh returned a non-array payload for the {what}",
                evidence={"argv": list(result.argv)},
            )
        return payload

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
    # A PR with no description answers with an empty string, which is a real
    # state a reviewer may need to fault. An absent or null field is a read that
    # did not deliver the body, and a credential-free lane has no second chance
    # at it, so it fails closed here rather than becoming a silent empty body.
    body = payload.get("body")
    if not isinstance(body, str):
        raise GitHubError(
            "pull request payload is missing its body; a reviewer is handed this "
            "text as the change's stated contract and cannot read it for itself",
            evidence={"repo": repo, "pr": number, "field": "body"},
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
        body=body,
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


def _flatten_pages(payload: list[Any]) -> list[Any]:
    """The items of a ``gh api --paginate --slurp`` response, in page order.

    ``--slurp`` wraps each page's array in an outer array, so the items are
    flattened one page at a time and never reordered: the loop compares artifact
    ids across two reads of the same surface, and it can only do that if the same
    PR always flattens the same way. A page that is an object rather than an
    array is kept as a single item so a one-element response is not silently
    dropped; validating it is the per-item parser's job.
    """
    return [
        item for page in payload for item in (page if isinstance(page, list) else [page])
    ]


def _review_from(payload: object) -> Comment:
    """One submitted review from the REST API.

    A review may legitimately carry an empty body — an approval with no text —
    so an empty body is data here, not an error. It simply cannot satisfy an
    artifact readback, which needs the declaration block and the signature.
    """
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
    if (
        not isinstance(identifier, (int, str))
        or isinstance(identifier, bool)
        or str(identifier) == ""
    ):
        raise GitHubError("review payload has no stable id", evidence={"author": login})
    body = payload.get("body")
    if body is not None and not isinstance(body, str):
        raise GitHubError("review payload has an unusable body", evidence={"author": login})
    commit_id = payload.get("commit_id")
    if commit_id is not None and not isinstance(commit_id, str):
        raise GitHubError("review payload has an unusable commit_id", evidence={"author": login})
    state = payload.get("state")
    if state is not None and not isinstance(state, str):
        raise GitHubError("review payload has an unusable state", evidence={"author": login})
    return Comment(
        # Namespaced, because a review id and a comment id are two different
        # counters and the loop keeps both in one set of run-owned identities.
        identifier=f"review:{identifier}",
        author=login,
        body=body or "",
        url=str(payload.get("html_url") or ""),
        kind="review",
        commit_id=(commit_id or "").lower(),
        state=(state or "").upper(),
    )


def _inline_comment_from(payload: object) -> InlineComment:
    """One inline review comment from the REST API."""
    if not isinstance(payload, dict):
        raise GitHubError("inline comment payload is not an object")
    user = payload.get("user")
    login = str(user.get("login") or "") if isinstance(user, dict) else ""
    if not login:
        raise GitHubError(
            "inline comment payload has no author login",
            evidence={"comment_id": str(payload.get("id") or "")},
        )
    identifier = payload.get("id")
    if not isinstance(identifier, (int, str)) or isinstance(identifier, bool):
        raise GitHubError("inline comment payload has no stable id", evidence={"author": login})
    body = payload.get("body")
    if body is not None and not isinstance(body, str):
        raise GitHubError("inline comment payload has an unusable body", evidence={"author": login})
    line = payload.get("line")
    commit_id = payload.get("commit_id")
    return InlineComment(
        identifier=f"inline:{identifier}",
        author=login,
        body=body or "",
        path=str(payload.get("path") or ""),
        line=line if isinstance(line, int) and not isinstance(line, bool) else None,
        commit_id=(commit_id if isinstance(commit_id, str) else "").lower(),
        url=str(payload.get("html_url") or ""),
    )


def _check_runs_from(pages: list[Any]) -> tuple[tuple[CheckRun, ...], bool]:
    """Every check run for one commit, and whether every page of them arrived.

    The REST response states ``total_count`` for the whole set, so this is one
    of the few surfaces where "complete" is a fact rather than an assumption.
    """
    runs: list[CheckRun] = []
    total: int | None = None
    for page in pages:
        if not isinstance(page, dict):
            raise GitHubError("check-run payload is not an object")
        reported = page.get("total_count")
        if total is None and isinstance(reported, int) and not isinstance(reported, bool):
            total = reported
        raw = page.get("check_runs")
        if not isinstance(raw, list):
            raise GitHubError("check-run payload has no check_runs array")
        for item in raw:
            if not isinstance(item, dict):
                raise GitHubError("check-run entry is not an object")
            runs.append(
                CheckRun(
                    name=str(item.get("name") or ""),
                    status=str(item.get("status") or ""),
                    conclusion=str(item.get("conclusion") or ""),
                    url=str(item.get("html_url") or ""),
                )
            )
    return tuple(runs), total is not None and len(runs) == total


# ``gh pr view --json closingIssuesReferences`` asks for a single page. A full
# one is indistinguishable from a truncated one, so completeness is claimed
# only below it.
_CLOSING_ISSUES_PAGE = 100


def _linked_issues_from(payload: dict[str, Any]) -> tuple[tuple[LinkedIssue, ...], bool]:
    """The issues this PR declares it closes, and whether that list is whole.

    A PR that closes nothing answers with an explicit ``[]``. An absent or null
    field is a different fact — the requested field did not come back — and it
    is the one that must not be rounded up into a complete empty surface, or a
    reviewer is handed "this PR closes nothing" as a proven statement about a
    read that never happened.
    """
    raw = payload.get("closingIssuesReferences")
    if not isinstance(raw, list):
        raise GitHubError(
            "closingIssuesReferences is missing, null, or not an array; an absent "
            "field is not a PR that provably closes nothing",
            evidence={"found": "null" if raw is None else type(raw).__name__},
        )
    issues: list[LinkedIssue] = []
    for item in raw:
        if not isinstance(item, dict):
            raise GitHubError("closing issue reference is not an object")
        number = item.get("number")
        if not isinstance(number, int) or isinstance(number, bool):
            raise GitHubError("closing issue reference has no issue number")
        issues.append(
            LinkedIssue(
                number=number,
                title=str(item.get("title") or ""),
                state=str(item.get("state") or ""),
                url=str(item.get("url") or ""),
            )
        )
    return tuple(issues), len(issues) < _CLOSING_ISSUES_PAGE


def _governing_issue_from(payload: dict[str, Any], *, expected: int) -> GoverningIssue:
    """One configured governing issue, held to the number that was asked for.

    The body is the contract, so a payload without one is not a thin issue: it
    is a read that did not deliver the thing the reviewer is judged against.
    """
    number = payload.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number != expected:
        raise GitHubError(
            "governing issue payload is for a different issue",
            evidence={"expected": expected, "found": number if isinstance(number, int) else None},
        )
    body = payload.get("body")
    if not isinstance(body, str):
        raise GitHubError(
            "governing issue payload has no body; the issue body is the task "
            "contract a credential-free reviewer judges this change against",
            evidence={"issue": expected, "field": "body"},
        )
    return GoverningIssue(
        number=number,
        title=str(payload.get("title") or ""),
        state=str(payload.get("state") or ""),
        body=body,
        url=str(payload.get("url") or ""),
    )


__all__ = [
    "CheckRun",
    "Comment",
    "GhCliGitHub",
    "GitHubBoundary",
    "GoverningIssue",
    "InlineComment",
    "LinkedIssue",
    "PullRequest",
    "ReviewEvidence",
]
