"""The injectable GitHub boundary.

The loop reads GitHub for four things: the live PR (to bind the exact
``headRefOid``), the PR conversation comments (to read back the builder's signed
fix comment), the submitted reviews (to read back each reviewer lane's published
artifact, and for their states), and the inline review threads with their
resolution state (so human feedback nobody resolved is an input to the run's
conclusion rather than something it never looked at). It never writes.

That split is the whole trust model. The trusted agents do their own work on
GitHub — the builder pushes, comments, and signs; the reviewers publish their
own role-signed reviews or comments under their own configured login — and this
boundary exists so the loop can check what actually landed instead of believing
what a lane printed about itself.

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

_PR_FIELDS = "number,state,isDraft,title,url,headRefName,headRefOid,baseRefName"

# ``$endCursor`` is the variable ``gh api graphql --paginate`` supplies, so the
# threads of a heavily reviewed PR cannot silently stop at the first page.
_REVIEW_THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          comments(first: 100) {
            nodes { id url body author { login } }
          }
        }
      }
    }
  }
}
"""


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
    """One published PR artifact — a conversation comment or a review.

    ``identifier`` is GitHub's own id for the artifact. It is the only field
    here that is stable and not attacker-chosen: an author login can be
    impersonated only by controlling that account, but a body — signature, role
    line, head SHA and all — can be copied verbatim by anybody who can comment.
    The loop therefore snapshots these ids before it invokes a trusted agent and
    accepts only an id it had not already seen.

    ``commit_id`` is set for submitted reviews, where GitHub itself records the
    commit reviewed. When it is present it is a stronger head binding than
    anything in the body, so the loop prefers it.
    """

    identifier: str
    author: str
    body: str
    url: str = ""
    kind: str = "comment"
    commit_id: str = ""
    state: str = ""


@dataclass(frozen=True)
class ReviewThread:
    """One inline review thread, with the resolution state GitHub itself records.

    ``is_resolved`` and ``is_outdated`` are the only parts of a thread that say
    whether its conversation is still live, and neither can be asserted by
    writing prose: resolving a thread is an action on GitHub, and a thread goes
    outdated when the lines it was anchored to stop existing. That is why they
    are read here rather than inferred from what the comments say.
    """

    identifier: str
    is_resolved: bool
    is_outdated: bool
    comments: tuple[Comment, ...] = ()
    path: str = ""

    @property
    def authors(self) -> tuple[str, ...]:
        seen: list[str] = []
        for comment in self.comments:
            if comment.author not in seen:
                seen.append(comment.author)
        return tuple(seen)


class GitHubBoundary(Protocol):
    """Injection seam for every GitHub read the loop performs."""

    def pull_request(self, repo: str, number: int) -> PullRequest: ...

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]: ...

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]: ...

    def review_threads(self, repo: str, number: int) -> tuple[ReviewThread, ...]: ...


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

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]:
        """Submitted reviews, read through the REST API for their ``commit_id``.

        ``gh pr view --json reviews`` omits the commit a review was submitted
        against, and that field is the head binding, so this one read goes
        through ``gh api`` instead.
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
        # ``--slurp`` wraps the pages, so the payload is a list of page arrays.
        # A PR reviewed more times than one page holds must not silently lose
        # the page the current head's artifact is on.
        flattened = [
            item
            for page in payload
            for item in (page if isinstance(page, list) else [page])
        ]
        return tuple(_review_from(item) for item in flattened)

    def review_threads(self, repo: str, number: int) -> tuple[ReviewThread, ...]:
        """Inline review threads and their resolution state, through GraphQL.

        Resolution and outdated-ness exist only in GraphQL — the REST review-comment
        endpoints expose neither — so this one read goes through ``gh api graphql``.
        """
        owner, _, name = repo.partition("/")
        payload = self._json_list(
            [
                self._gh,
                "api",
                "graphql",
                "--paginate",
                "--slurp",
                "-F",
                f"owner={owner}",
                "-F",
                f"name={name}",
                "-F",
                f"number={number}",
                "-f",
                f"query={_REVIEW_THREADS_QUERY}",
            ],
            what="pull request review threads",
        )
        threads: list[ReviewThread] = []
        for page in payload:
            for node in _thread_nodes(page):
                threads.append(_thread_from(node))
        return tuple(threads)

    def _json(self, argv: Sequence[str], *, what: str) -> dict[str, Any]:
        payload = self._payload(argv, what=what)
        if not isinstance(payload, dict):
            raise GitHubError(
                f"gh returned a non-object payload for the {what}",
                evidence={"argv": list(argv)},
            )
        return payload

    def _json_list(self, argv: Sequence[str], *, what: str) -> list[Any]:
        payload = self._payload(argv, what=what)
        if not isinstance(payload, list):
            raise GitHubError(
                f"gh returned a non-array payload for the {what}",
                evidence={"argv": list(argv)},
            )
        return payload

    def _payload(self, argv: Sequence[str], *, what: str) -> Any:
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


def _review_from(payload: object) -> Comment:
    """One submitted review from the REST API.

    A review may legitimately carry an empty body — an approval with no text —
    so an empty body is data here, not an error. It simply cannot satisfy an
    artifact readback, which needs the role line and the head.
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
    if not isinstance(identifier, (int, str)) or isinstance(identifier, bool) or str(identifier) == "":
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
        identifier=f"review:{identifier}",
        author=login,
        body=body or "",
        url=str(payload.get("html_url") or ""),
        kind="review",
        commit_id=(commit_id or "").lower(),
        state=(state or "").upper(),
    )


def _thread_nodes(page: object) -> list[Any]:
    """The ``reviewThreads`` nodes of one GraphQL page, or nothing for an empty PR."""
    if not isinstance(page, dict):
        raise GitHubError("review-thread payload is not an object")
    cursor: Any = page.get("data", page)
    for key in ("repository", "pullRequest", "reviewThreads"):
        if not isinstance(cursor, dict):
            raise GitHubError(
                "review-thread payload is missing the reviewThreads connection",
                evidence={"missing_at": key},
            )
        cursor = cursor.get(key)
    if cursor is None:
        return []
    if not isinstance(cursor, dict):
        raise GitHubError("review-thread payload has an unusable reviewThreads connection")
    nodes = cursor.get("nodes")
    if nodes is None:
        return []
    if not isinstance(nodes, list):
        raise GitHubError("review-thread payload has an unusable nodes array")
    return nodes


def _thread_from(node: object) -> ReviewThread:
    """One review thread. Resolution state is required; an absent flag is not 'resolved'."""
    if not isinstance(node, dict):
        raise GitHubError("review thread is not an object")
    identifier = node.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise GitHubError("review thread has no stable id")
    resolved = node.get("isResolved")
    outdated = node.get("isOutdated")
    if not isinstance(resolved, bool) or not isinstance(outdated, bool):
        raise GitHubError(
            "review thread is missing its resolution state",
            evidence={"thread": identifier},
        )
    raw = node.get("comments")
    items = raw.get("nodes") if isinstance(raw, dict) else None
    if items is None:
        items = []
    if not isinstance(items, list):
        raise GitHubError(
            "review thread has an unusable comments array", evidence={"thread": identifier}
        )
    return ReviewThread(
        identifier=identifier,
        is_resolved=resolved,
        is_outdated=outdated,
        comments=tuple(_thread_comment_from(item, thread=identifier) for item in items),
        path=str(node.get("path") or ""),
    )


def _thread_comment_from(payload: object, *, thread: str) -> Comment:
    if not isinstance(payload, dict):
        raise GitHubError("review-thread comment is not an object", evidence={"thread": thread})
    author = payload.get("author")
    login = str(author.get("login") or "") if isinstance(author, dict) else ""
    if not login:
        # A deleted account leaves ``author: null``. That is real data, and the
        # thread it sits in still has to be counted, so it is named rather than
        # dropped — the resolution state is what decides, not the login.
        login = "<unknown>"
    identifier = payload.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise GitHubError("review-thread comment has no stable id", evidence={"thread": thread})
    body = payload.get("body")
    if body is not None and not isinstance(body, str):
        raise GitHubError(
            "review-thread comment has an unusable body", evidence={"thread": thread}
        )
    return Comment(
        identifier=identifier,
        author=login,
        body=body or "",
        url=str(payload.get("url") or ""),
        kind="review-thread-comment",
    )


__all__ = [
    "Comment",
    "GhCliGitHub",
    "GitHubBoundary",
    "PullRequest",
    "ReviewThread",
]
