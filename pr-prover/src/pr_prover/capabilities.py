"""Narrow, launcher-owned GitHub operations. The child never holds a credential.

A child used to be handed a GitHub token and told which things not to do with
it. That is not a boundary: a token that can write contents on a repository can
push any ref, and a token with the right scope can merge. The prompt saying
"never merge" is a request, and the capability enum in :mod:`.identities` only
described what the launcher *intended* to grant.

So no child gets a credential at all. Each lane is given the path of a unix
socket in a launcher-owned directory (``PR_PROVER_CAPABILITY_SOCKET``) and a
small shim on its ``PATH``:

    pr-prover-cap push
    pr-prover-cap comment --body-file PATH
    pr-prover-cap review  --body-file PATH

The shim carries no authority either. It serialises one request and hands it to
this module, which runs inside the launcher process, holds the scoped
credential, and composes the whole ``git``/``gh`` argv array itself from the
:class:`~.launchers.BoundContext` the run is bound to. A request names an
operation and, for the two that post text, a body. It cannot name a repository,
a pull request, a ref, a branch, a commit, or a force flag — those are not
fields of the request, so "push somewhere else" and "merge this" are not
expressible rather than merely refused.

Three operations exist, one per capability, and the names are the same strings
:mod:`.identities` uses::

    push-branch   push the lane worktree's HEAD to the one bound branch
    comment-pr    post one conversation comment on the one bound PR
    review-pr     submit one COMMENT review on the one bound PR at the bound head

An operation runs only if the lane's identity declares the capability of the
same name, so a reviewer that asks to push is refused by the same mechanism that
would refuse an unknown operation.

What is enforced here, structurally:

* the push target is ``https://github.com/<bound repo>.git`` and the refspec is
  ``<worktree HEAD>:refs/heads/<bound branch>``, both composed from the bound
  context; no ``--force``, no ``--delete``, no ``--mirror``, no tags;
* a review is always submitted with ``event=COMMENT`` against the bound head, so
  a child cannot approve a pull request or file a blocking review;
* a comment goes to the bound repository's bound issue/PR number only;
* the total number of operations one lane may perform is capped, so a lane that
  loops cannot post without bound.

The socket lives in a mode-0700 directory the launcher creates and removes, and
the socket itself is mode 0600. A different lane gets a different socket, and a
lane's socket is torn down when the lane ends.

**A socket path is not an authenticator.** Mode 0700 keeps other *users* out; it
does nothing about another process running as this user, and every lane on a
machine runs as the same user. A lane that walked the launcher's scratch tree
could find a sibling lane's socket and spend that lane's capabilities under that
lane's identity. So each channel is bound to one cryptographically random
per-lane secret, issued to exactly one lane in its narrow child environment
(``PR_PROVER_CAPABILITY_SECRET``), and every request must present it as its
first line. The comparison is constant time and happens *before* the request is
parsed, so a wrong or missing secret means no JSON is decoded, no operation is
authorised, and no ``git`` or ``gh`` subprocess is started at all. The strict
sandbox policy (:mod:`.sandbox`) allows a lane exactly one unix socket — its
own — so the two defences are independent: one lane cannot reach another's
socket, and could not spend it if it did.

**Closing is deterministic.** :meth:`CapabilityChannel.close` stops accepting,
closes the listening socket, tells the broker to refuse new work, waits for the
handlers it already accepted, and — if any is still running — cancels the
``git``/``gh`` process groups those handlers hold before joining again. Only
then is the socket removed. When ``close()`` returns, no accepted request can
still take effect and no subprocess this broker started is still alive, which is
what lets the launcher remove the lane's scratch and worktree behind it.
"""
from __future__ import annotations

import hmac
import json
import re
import secrets
import socket
import socketserver
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .childenv import MIN_CAPABILITY_SECRET_CHARS
from .commands import CommandRunner, LaunchWatch, run_watched
from .errors import CapabilityRefused
from .redaction import evidence as redact_evidence

# The operations, which are exactly the capability names in :mod:`.identities`.
PUSH_BRANCH = "push-branch"
COMMENT_PR = "comment-pr"
REVIEW_PR = "review-pr"

# What a request for each operation may contain, in full. Anything else — a
# repo, a ref, a branch, a sha, a force flag — is an unknown field and refused.
REQUEST_FIELDS: Mapping[str, frozenset[str]] = {
    PUSH_BRANCH: frozenset({"operation"}),
    COMMENT_PR: frozenset({"operation", "body"}),
    REVIEW_PR: frozenset({"operation", "body"}),
}

# The verbs the shim exposes, mapped onto operations.
SHIM_VERBS: Mapping[str, str] = {
    "push": PUSH_BRANCH,
    "comment": COMMENT_PR,
    "review": REVIEW_PR,
}

GITHUB_HOST = "https://github.com"
MAX_REQUEST_BYTES = 1 << 20
MAX_BODY_CHARS = 60000
# One lane's whole budget of brokered operations. A builder needs a push and a
# comment; a reviewer needs one artifact. The cap is what stops a lane that
# loops from posting without bound.
MAX_OPERATIONS = 16
# AF_UNIX paths are short on every platform this runs on (104 bytes on macOS,
# 108 on Linux). A path that would be truncated is a channel nobody can reach.
MAX_SOCKET_PATH = 100
# How often the serving thread checks whether it has been asked to stop. Short,
# because a lane's channel is closed the moment the lane ends and the launcher
# waits for that before it removes the lane's scratch.
SHUTDOWN_POLL_SECONDS = 0.01
# How long a lane's already-accepted handlers get to finish once the channel has
# stopped accepting, before their subprocesses are cancelled; then how long they
# get after the cancellation. Both bounded: close() must return.
DRAIN_SECONDS = 10.0
CANCEL_JOIN_SECONDS = 15.0
# How long the serving thread gets to notice it has been asked to stop.
SERVE_JOIN_SECONDS = 10.0

# One lane secret, in hex characters. 64 is 256 bits.
SECRET_CHARS = 64

# What a caller sees when it presents the wrong secret, or none. Deliberately
# the same string either way: the reply is not an oracle for which lane a socket
# belongs to.
AUTH_REFUSED = (
    "this capability channel is bound to one lane; the request did not present "
    "that lane's secret"
)

_REPO = re.compile(r"\A[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\Z")
_BRANCH = re.compile(r"\A(?!-)[A-Za-z0-9._/-]{1,255}\Z")
_FULL_SHA = re.compile(r"\A[0-9a-f]{40}\Z")

SHIM_NAME = "pr-prover-cap"

SHIM_SOURCE = '''\
"""The capability shim: the only way a pr-prover child reaches GitHub.

This program holds no credential. It serialises one request onto the unix
socket named by PR_PROVER_CAPABILITY_SOCKET, authenticated with the per-lane
secret in PR_PROVER_CAPABILITY_SECRET, and prints what the launcher, which does
hold the credential, says happened.

The secret comes from this lane's environment and is written as the first line
of the request. It is never passed on argv, where every process on the machine
could read it, and never read from a file the request itself names.
"""
import json
import os
import socket
import sys

USAGE = (
    "usage: pr-prover-cap push\\n"
    "       pr-prover-cap comment --body-file PATH\\n"
    "       pr-prover-cap review --body-file PATH"
)
VERBS = {"push": "push-branch", "comment": "comment-pr", "review": "review-pr"}


def fail(message, code=2):
    sys.stderr.write("pr-prover-cap: " + message + "\\n")
    raise SystemExit(code)


def main(argv):
    if not argv:
        fail(USAGE)
    operation = VERBS.get(argv[0])
    if operation is None:
        fail(USAGE)
    request = {"operation": operation}
    rest = argv[1:]
    if operation == "push-branch":
        if rest:
            fail(USAGE)
    else:
        if len(rest) != 2 or rest[0] != "--body-file":
            fail(USAGE)
        try:
            with open(rest[1], "r", encoding="utf-8") as handle:
                request["body"] = handle.read()
        except OSError as exc:
            fail("cannot read body file: %s" % exc)
    path = os.environ.get("PR_PROVER_CAPABILITY_SOCKET", "")
    if not path:
        fail("this lane has no capability channel")
    secret = os.environ.get("PR_PROVER_CAPABILITY_SECRET", "")
    if not secret:
        fail("this lane has no capability channel secret")
    frame = secret.encode("utf-8") + b"\\n" + json.dumps(request).encode("utf-8")
    try:
        channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        channel.connect(path)
        channel.sendall(frame)
        channel.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            data = channel.recv(65536)
            if not data:
                break
            chunks.append(data)
        channel.close()
    except OSError as exc:
        fail("capability channel unavailable: %s" % exc)
    try:
        reply = json.loads(b"".join(chunks).decode("utf-8"))
    except ValueError:
        fail("capability channel returned an unreadable reply")
    if not isinstance(reply, dict):
        fail("capability channel returned an unreadable reply")
    if not reply.get("ok"):
        fail(str(reply.get("error") or "refused"), 1)
    sys.stdout.write(json.dumps(reply, sort_keys=True) + "\\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''


@dataclass(frozen=True)
class CapabilityScope:
    """The exact repository, pull request, branch, and commit a channel serves."""

    repo: str
    pr: int
    branch: str
    head: str

    def __post_init__(self) -> None:
        if not _REPO.match(self.repo):
            raise CapabilityRefused(
                "a capability channel must be bound to one 'owner/name' repository",
                evidence={"repo": self.repo},
            )
        if not isinstance(self.pr, int) or isinstance(self.pr, bool) or self.pr < 1:
            raise CapabilityRefused(
                "a capability channel must be bound to one pull request number",
                evidence={"pr": self.pr},
            )
        if not _BRANCH.match(self.branch) or ".." in self.branch:
            raise CapabilityRefused(
                "a capability channel must be bound to one usable branch name",
                evidence={"branch": self.branch},
            )
        if not _FULL_SHA.match(self.head):
            raise CapabilityRefused(
                "a capability channel must be bound to one full 40-hex head",
                evidence={"head": self.head},
            )

    @property
    def remote_url(self) -> str:
        return f"{GITHUB_HOST}/{self.repo}.git"

    @property
    def refspec_target(self) -> str:
        return f"refs/heads/{self.branch}"


class CapabilityBroker:
    """Performs the three narrow operations, holding the credential itself.

    ``credential_env`` is the launcher-side environment that carries the scoped
    token. It is built for this object and handed to ``git`` and ``gh`` here;
    it is never given to a child, and nothing in this class returns it.
    """

    def __init__(
        self,
        *,
        runner: CommandRunner,
        scope: CapabilityScope,
        capabilities: frozenset[str],
        worktree: Path,
        credential_env: Mapping[str, str],
        scratch: Path,
        git: str = "git",
        gh: str = "gh",
        timeout: float = 600.0,
        on_event: Callable[[str], None] | None = None,
        watch: LaunchWatch | None = None,
    ) -> None:
        self._runner = runner
        self._scope = scope
        self._capabilities = frozenset(capabilities)
        self._worktree = Path(worktree)
        self._credential_env = dict(credential_env)
        self._scratch = Path(scratch)
        self._git = git
        self._gh = gh
        self._timeout = timeout
        self._on_event = on_event
        self._lock = threading.Lock()
        self._performed = 0
        # Deliberately not guarded by ``_lock``: that lock is held for the whole
        # of an operation, subprocess included, so a closer that had to take it
        # could not interrupt the very thing it is trying to stop.
        self._stopped = threading.Event()
        self._watch = watch if watch is not None else LaunchWatch()
        self.granted: list[str] = []
        self.refused: list[str] = []

    # -- shutdown ----------------------------------------------------------
    @property
    def watch(self) -> LaunchWatch:
        """The process groups this broker currently has open."""
        return self._watch

    @property
    def stopped(self) -> bool:
        return self._stopped.is_set()

    def stop(self) -> None:
        """Refuse every operation from now on. Work already running is untouched."""
        self._stopped.set()

    def cancel(self) -> tuple[int, ...]:
        """Stop, then terminate every ``git``/``gh`` process group still running.

        Latching: after this returns, an operation that was mid-flight cannot
        start another subprocess either, so a handler cannot outrun the closer by
        being between two commands of the same operation.
        """
        self._stopped.set()
        return self._watch.cancel()

    # -- request handling --------------------------------------------------
    def handle(self, raw: str) -> dict[str, object]:
        """Parse one request and perform it, or return a refusal. Never raises."""
        try:
            operation, body = self._parse(raw)
            with self._lock:
                self._authorise(operation)
                self._performed += 1
                result = self._perform(operation, body)
        except CapabilityRefused as exc:
            self.refused.append(exc.message)
            self._event(f"capability refused: {exc.message}")
            return {"ok": False, "error": exc.message, "evidence": exc.evidence}
        except Exception as exc:  # pragma: no cover - defensive; a child must never see a traceback
            self.refused.append(str(exc))
            self._event(f"capability failed: {type(exc).__name__}")
            return {"ok": False, "error": f"the capability broker failed: {type(exc).__name__}"}
        self.granted.append(operation)
        self._event(f"capability granted: {operation} on {self._scope.repo}#{self._scope.pr}")
        return {"ok": True, **result}

    def _parse(self, raw: str) -> tuple[str, str | None]:
        try:
            payload = json.loads(raw or "")
        except ValueError as exc:
            raise CapabilityRefused(
                "capability request is not valid JSON", evidence={"error": str(exc)}
            ) from exc
        if not isinstance(payload, dict):
            raise CapabilityRefused("capability request must be a JSON object")
        operation = payload.get("operation")
        if not isinstance(operation, str) or operation not in REQUEST_FIELDS:
            raise CapabilityRefused(
                "this launcher has no such operation; the vocabulary is closed and has "
                "no merge, approve, deploy, admin, or arbitrary-command form",
                evidence={"operation": operation, "operations": sorted(REQUEST_FIELDS)},
            )
        unknown = sorted(set(payload) - REQUEST_FIELDS[operation])
        if unknown:
            raise CapabilityRefused(
                "a capability request cannot name its own repository, pull request, "
                "ref, branch, commit, or flags; those come from the bound context",
                evidence={"operation": operation, "unknown_fields": unknown},
            )
        if operation == PUSH_BRANCH:
            return operation, None
        return operation, _checked_body(payload.get("body"))

    def _authorise(self, operation: str) -> None:
        if self._stopped.is_set():
            raise CapabilityRefused(
                "this lane's capability channel is closing; no further operation is "
                "accepted on it",
                evidence={"operation": operation, "repo": self._scope.repo},
            )
        if operation not in self._capabilities:
            raise CapabilityRefused(
                "this lane's identity does not carry the capability for that operation",
                evidence={
                    "operation": operation,
                    "capabilities": sorted(self._capabilities),
                    "repo": self._scope.repo,
                    "pr": self._scope.pr,
                },
            )
        if self._performed >= MAX_OPERATIONS:
            raise CapabilityRefused(
                "this lane has spent its whole budget of brokered operations",
                evidence={"performed": self._performed, "maximum": MAX_OPERATIONS},
            )

    def _perform(self, operation: str, body: str | None) -> dict[str, object]:
        if operation == PUSH_BRANCH:
            return self._push()
        if operation == COMMENT_PR:
            return self._comment(body or "")
        return self._review(body or "")

    # -- operations --------------------------------------------------------
    def push_argv(self, head: str) -> tuple[str, ...]:
        """The exact push argv this broker composes. Bound context only."""
        scope = self._scope
        return (
            self._git,
            "-C",
            str(self._worktree),
            "-c",
            "credential.helper=",
            "-c",
            f"credential.{GITHUB_HOST}.helper=!{self._gh} auth git-credential",
            "push",
            "--no-verify",
            "--",
            scope.remote_url,
            f"{head}:{scope.refspec_target}",
        )

    def _push(self) -> dict[str, object]:
        head = self._worktree_head()
        if head == self._scope.head:
            raise CapabilityRefused(
                "the lane worktree still points at the head this run is bound to; "
                "there is nothing new to push",
                evidence={"head": head, "bound_head": self._scope.head},
            )
        result = self._run(self.push_argv(head), what="push the bound branch")
        return {
            "operation": PUSH_BRANCH,
            "repo": self._scope.repo,
            "branch": self._scope.branch,
            "head": head,
            "detail": redact_evidence(result, limit=2000),
        }

    def _comment(self, body: str) -> dict[str, object]:
        scope = self._scope
        payload = self._api(
            f"repos/{scope.repo}/issues/{scope.pr}/comments",
            {"body": body},
            what="comment on the bound pull request",
        )
        return {
            "operation": COMMENT_PR,
            "repo": scope.repo,
            "pr": scope.pr,
            "id": str(payload.get("id") or ""),
            "url": str(payload.get("html_url") or ""),
        }

    def _review(self, body: str) -> dict[str, object]:
        scope = self._scope
        # event is fixed at COMMENT and commit_id at the bound head: a child
        # cannot approve, cannot request changes, and cannot file a review
        # against some other commit.
        payload = self._api(
            f"repos/{scope.repo}/pulls/{scope.pr}/reviews",
            {"body": body, "event": "COMMENT", "commit_id": scope.head},
            what="review the bound pull request",
        )
        return {
            "operation": REVIEW_PR,
            "repo": scope.repo,
            "pr": scope.pr,
            "head": scope.head,
            "state": str(payload.get("state") or ""),
            "id": str(payload.get("id") or ""),
            "url": str(payload.get("html_url") or ""),
        }

    # -- plumbing ----------------------------------------------------------
    def _worktree_head(self) -> str:
        raw = self._run(
            (self._git, "-C", str(self._worktree), "rev-parse", "HEAD"),
            what="read the lane worktree head",
        )
        head = raw.strip().lower()
        if not _FULL_SHA.match(head):
            raise CapabilityRefused(
                "the lane worktree does not resolve to a full 40-hex commit",
                evidence={"rev_parse": redact_evidence(raw, limit=200)},
            )
        return head

    def _api(self, endpoint: str, payload: Mapping[str, object], *, what: str) -> dict[str, object]:
        path = Path(
            tempfile.mkstemp(prefix="cap-", suffix=".json", dir=str(self._scratch))[1]
        )
        try:
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            path.chmod(0o600)
            raw = self._run(
                (
                    self._gh,
                    "api",
                    "--method",
                    "POST",
                    endpoint,
                    "--header",
                    "Accept: application/vnd.github+json",
                    "--input",
                    str(path),
                ),
                what=what,
            )
        finally:
            path.unlink(missing_ok=True)
        try:
            decoded = json.loads(raw or "null")
        except ValueError as exc:
            raise CapabilityRefused(
                f"GitHub returned an unreadable payload when asked to {what}",
                evidence={"error": str(exc)},
            ) from exc
        if not isinstance(decoded, dict):
            raise CapabilityRefused(
                f"GitHub returned a non-object payload when asked to {what}"
            )
        return decoded

    def _run(self, argv: Sequence[str], *, what: str) -> str:
        result = run_watched(
            self._runner,
            list(argv),
            cwd=self._worktree,
            env=self._credential_env,
            timeout=self._timeout,
            watch=self._watch,
        )
        if not result.ok:
            raise CapabilityRefused(
                f"could not {what}",
                evidence={
                    "returncode": result.returncode,
                    "timed_out": result.timed_out,
                    "stderr": redact_evidence(result.stderr, limit=1000),
                },
            )
        return result.stdout or ""

    def _event(self, message: str) -> None:
        if self._on_event is not None:
            self._on_event(message)


def _checked_body(body: object) -> str:
    if not isinstance(body, str) or not body.strip():
        raise CapabilityRefused("this operation needs a non-empty body")
    if len(body) > MAX_BODY_CHARS:
        raise CapabilityRefused(
            "this body is longer than GitHub accepts",
            evidence={"length": len(body), "maximum": MAX_BODY_CHARS},
        )
    if "\x00" in body:
        raise CapabilityRefused("this body contains a NUL byte")
    return body


def authenticates(presented: bytes, secret: str) -> bool:
    """Constant-time check of one presented secret against this lane's."""
    return hmac.compare_digest(presented, secret.encode("utf-8"))


def split_frame(raw: bytes) -> tuple[bytes, bytes]:
    """Split a request frame into ``(presented secret, request bytes)``.

    A frame with no newline has presented nothing, and is returned as such
    rather than being treated as an unauthenticated request body.
    """
    presented, separator, body = raw.partition(b"\n")
    if not separator:
        return b"", b""
    return presented, body


class _ChannelServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    # socketserver's own join on close is unbounded and happens inside
    # ``server_close``. This class tracks its handlers itself so that closing can
    # drain, then cancel, then join, in that order and within a bound.
    block_on_close = False
    allow_reuse_address = False

    def __init__(
        self,
        path: str,
        broker: CapabilityBroker,
        *,
        secret: str,
        on_event: Callable[[str], None] | None = None,
    ) -> None:
        self.broker = broker
        self.secret = secret
        self.on_event = on_event
        self.accepted = 0
        self.unauthenticated = 0
        self._handler_lock = threading.Lock()
        self._handlers: set[threading.Thread] = set()
        self._accepting = True
        super().__init__(path, _ChannelHandler)

    # -- accepting ---------------------------------------------------------
    def stop_accepting(self) -> None:
        with self._handler_lock:
            self._accepting = False

    def process_request(self, request: object, client_address: object) -> None:
        thread = threading.Thread(
            target=self.process_request_thread,
            args=(request, client_address),
            name="pr-prover-cap-handler",
            daemon=True,
        )
        with self._handler_lock:
            if not self._accepting:
                self.shutdown_request(request)  # type: ignore[arg-type]
                return
            self._handlers.add(thread)
            self.accepted += 1
        thread.start()

    def process_request_thread(self, request: object, client_address: object) -> None:
        try:
            super().process_request_thread(request, client_address)  # type: ignore[arg-type]
        finally:
            with self._handler_lock:
                self._handlers.discard(threading.current_thread())

    # -- draining ----------------------------------------------------------
    def live_handlers(self) -> tuple[threading.Thread, ...]:
        with self._handler_lock:
            return tuple(thread for thread in self._handlers if thread.is_alive())

    def join_handlers(self, grace: float) -> tuple[threading.Thread, ...]:
        """Join every accepted handler within ``grace`` seconds in total."""
        deadline = time.monotonic() + max(0.0, grace)
        for thread in self.live_handlers():
            thread.join(timeout=max(0.0, deadline - time.monotonic()))
        return self.live_handlers()

    def note_unauthenticated(self) -> None:
        with self._handler_lock:
            self.unauthenticated += 1
        if self.on_event is not None:
            self.on_event("capability refused: request did not present this lane's secret")


class _ChannelHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw = self.rfile.read(MAX_REQUEST_BYTES + 1)
        server: _ChannelServer = self.server  # type: ignore[assignment]
        if len(raw) > MAX_REQUEST_BYTES:
            self._reply({"ok": False, "error": "capability request is too large"})
            return
        presented, body = split_frame(raw)
        # Before parsing, before dispatch, and before anything reaches the
        # broker: a request that cannot prove it is this lane starts no
        # subprocess and learns nothing about what this channel is bound to.
        if not authenticates(presented, server.secret):
            server.note_unauthenticated()
            self._reply({"ok": False, "error": AUTH_REFUSED})
            return
        self._reply(server.broker.handle(body.decode("utf-8", "replace")))

    def _reply(self, response: Mapping[str, object]) -> None:
        try:
            self.wfile.write((json.dumps(response, sort_keys=True) + "\n").encode("utf-8"))
        except OSError:  # pragma: no cover - the caller went away, or we were cancelled
            return


class CapabilityChannel:
    """One lane's socket, served by one broker, for exactly that lane's lifetime.

    The channel mints its own secret. Nothing outside this object chooses it,
    and the only place it is meant to travel is the one lane's environment, via
    :attr:`secret`.
    """

    def __init__(
        self,
        broker: CapabilityBroker,
        *,
        label: str,
        on_event: Callable[[str], None] | None = None,
    ) -> None:
        self.broker = broker
        self.secret = secrets.token_hex(SECRET_CHARS // 2)
        if len(self.secret) < MIN_CAPABILITY_SECRET_CHARS:  # pragma: no cover - build-time
            raise CapabilityRefused(
                "a capability channel secret is shorter than the child environment "
                "policy accepts",
                evidence={"length": len(self.secret)},
            )
        self._on_event = on_event
        self._directory = Path(tempfile.mkdtemp(prefix="prcap-"))
        self._directory.chmod(0o700)
        self.path = self._directory / f"{label}.sock"
        if len(str(self.path)) > MAX_SOCKET_PATH:
            self._directory.rmdir()
            raise CapabilityRefused(
                "the capability socket path is too long for this platform; set TMPDIR "
                "to a shorter directory",
                evidence={"path": str(self.path), "maximum": MAX_SOCKET_PATH},
            )
        self._server = _ChannelServer(
            str(self.path), broker, secret=self.secret, on_event=on_event
        )
        self.path.chmod(0o600)
        # Set once close() could not account for every accepted handler. The
        # launcher turns it into a fail-closed stop rather than letting a run
        # continue past work it could not prove had finished.
        self.shutdown_error: CapabilityRefused | None = None
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            kwargs={"poll_interval": SHUTDOWN_POLL_SECONDS},
            name=f"pr-prover-cap-{label}",
            daemon=True,
        )
        self._thread.start()

    @property
    def unauthenticated(self) -> int:
        """How many requests failed to present this lane's secret."""
        server = getattr(self, "_server", None)
        return self._unauthenticated if server is None else server.unauthenticated

    def close(self) -> None:
        """Stop accepting, drain, cancel what is left, then remove the socket.

        The order is the whole point, and it is:

        1. stop accepting, so nothing new is taken on;
        2. stop the serving thread and close the listening socket, so a lane that
           kept the path cannot connect again;
        3. tell the broker to refuse, so a handler that has been accepted but has
           not yet authorised an operation performs none;
        4. wait :data:`DRAIN_SECONDS` for work already running to finish, because
           a push that is nearly done should be allowed to be done;
        5. cancel — terminate the ``git``/``gh`` process groups that are still
           running, ``SIGTERM`` then ``SIGKILL`` — and join again;
        6. only now remove the socket and its directory.

        Safe to call twice. Returns normally in every case; if a handler could
        not be accounted for, :attr:`shutdown_error` carries the refusal.
        """
        server = getattr(self, "_server", None)
        if server is not None:
            server.stop_accepting()
            server.shutdown()
            thread = getattr(self, "_thread", None)
            if thread is not None:
                thread.join(timeout=SERVE_JOIN_SECONDS)
                self._thread = None  # type: ignore[assignment]
            server.server_close()
            self.broker.stop()
            remaining = server.join_handlers(DRAIN_SECONDS)
            if remaining:
                groups = self.broker.cancel()
                self._event(
                    "capability channel cancelled "
                    f"{len(remaining)} handler(s) and {len(groups)} process group(s) on close"
                )
                remaining = server.join_handlers(CANCEL_JOIN_SECONDS)
            self._unauthenticated = server.unauthenticated
            self._server = None  # type: ignore[assignment]
            if remaining:
                self.shutdown_error = CapabilityRefused(
                    "a capability handler was still running after its channel was "
                    "closed, cancelled, and joined; refusing to report a run whose "
                    "brokered work cannot be accounted for",
                    evidence={
                        "handlers": len(remaining),
                        "drain_seconds": DRAIN_SECONDS,
                        "cancel_join_seconds": CANCEL_JOIN_SECONDS,
                    },
                )
        thread = getattr(self, "_thread", None)
        if thread is not None:
            thread.join(timeout=SERVE_JOIN_SECONDS)
            self._thread = None  # type: ignore[assignment]
        path = getattr(self, "path", None)
        if path is not None:
            Path(path).unlink(missing_ok=True)
        directory = getattr(self, "_directory", None)
        if directory is not None and Path(directory).is_dir():
            try:
                Path(directory).rmdir()
            except OSError:  # pragma: no cover - a leftover file is not worth failing a run
                pass

    def _event(self, message: str) -> None:
        if self._on_event is not None:
            self._on_event(message)

    def __enter__(self) -> CapabilityChannel:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    _unauthenticated = 0


def frame(secret: str, payload: Mapping[str, object]) -> bytes:
    """The wire form of one request: the lane secret, a newline, then the JSON."""
    return secret.encode("utf-8") + b"\n" + json.dumps(payload).encode("utf-8")


def request(
    path: Path | str, payload: Mapping[str, object], *, secret: str
) -> dict[str, object]:
    """Speak the channel protocol directly. Used by this package's own tests."""
    channel = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        channel.connect(str(path))
        channel.sendall(frame(secret, payload))
        channel.shutdown(socket.SHUT_WR)
        chunks: list[bytes] = []
        while True:
            data = channel.recv(65536)
            if not data:
                break
            chunks.append(data)
    finally:
        channel.close()
    decoded = json.loads(b"".join(chunks).decode("utf-8"))
    return decoded if isinstance(decoded, dict) else {"ok": False, "error": "unreadable reply"}


def write_shim(directory: Path) -> Path:
    """Write the capability shim into a launcher-owned ``bin`` directory."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    path = directory / SHIM_NAME
    path.write_text(f"#!{sys.executable}\n{SHIM_SOURCE}", encoding="utf-8")
    path.chmod(0o700)
    return path


__all__ = [
    "AUTH_REFUSED",
    "CANCEL_JOIN_SECONDS",
    "COMMENT_PR",
    "DRAIN_SECONDS",
    "GITHUB_HOST",
    "MAX_BODY_CHARS",
    "MAX_OPERATIONS",
    "PUSH_BRANCH",
    "REQUEST_FIELDS",
    "REVIEW_PR",
    "SHIM_NAME",
    "SHIM_SOURCE",
    "SHIM_VERBS",
    "CapabilityBroker",
    "CapabilityChannel",
    "CapabilityScope",
    "authenticates",
    "frame",
    "request",
    "split_frame",
    "write_shim",
]
