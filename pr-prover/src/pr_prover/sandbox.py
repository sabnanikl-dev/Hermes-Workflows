"""The code-owned strict sandbox policy for a Claude agent lane.

A Claude agent lane used to be confined by three things: an empty MCP config, a
narrow tool list on its argv, and a synthetic ``HOME``. None of those stops the
lane's own ``Bash`` from reading ``~/.ssh`` through an absolute path, writing
outside its worktree, or opening a socket to anywhere. Claude Code has an
OS-backed sandbox that does stop those, and this module is the only thing that
decides what it says.

Four properties make it a boundary rather than a suggestion:

**The launcher writes the settings file.** A fresh one per launch, under the
lane's own directory, mode 0600, passed on argv as ``--settings`` beside a
``--setting-sources`` entry that names no source. A run configuration cannot
supply a settings file, cannot add a settings *source*, and cannot edit the one
this module generates, because it never names it.

**The document is generated, then re-read and proved.** :func:`document` builds
it and :func:`assert_settings` checks the parsed JSON against
:data:`REQUIRED` — every key checked by the name Claude Code 2.1.219 actually
reads, with the exact value that key must carry. A key this launcher does not
own may not appear under ``sandbox`` at all (:data:`KNOWN_SANDBOX_KEYS`), so a
document cannot be made to *look* strict by carrying a spelling the client
ignores. The launcher calls the check on the bytes it just wrote and again
immediately before the spawn, so a later edit that loosens the first fails at
launch instead of shipping.

**Reads and writes are enumerated per lane, not per launcher — and they do not
work the same way.** This is the part that has to be read carefully, because
getting it wrong produced a policy that looked strict and refused every launch.

*Reads* nest. A broad ``denyRead`` closes a region and a more specific
``allowRead`` reopens a path inside it; Claude Code documents this, and a live
probe of 2.1.219 confirms it. So the launcher's whole scratch root and the
operator's whole home are denied for reading, and exactly this lane's roots —
its scratch, home, runtime, input, settings file, and the authorised worktree —
are named back. A sibling lane matches only the broad denial, so it stays
unreadable.

*Writes do not nest.* A ``denyWrite`` region is a hard denial, and a nested
``allowWrite`` does not reopen it. A live probe proved that: with the operator's
home and the launcher's scratch root broadly denied for writing, the builder's
own worktree, the lane's own scratch, and the lane's own synthetic home were all
refused with ``Operation not permitted``, even though every one of them was named
in ``allowWrite``. So the write policy is built the other way round. It leans on
Claude's own default write boundary — the working directory and the session
temporary directory, and nothing else — and adds exactly this lane's writable
roots to it. ``denyWrite`` carries only *exact immutable paths*: the worktree's
Git metadata, a reviewer's worktree, this lane's runtime, its frozen input, its
settings file, the empty MCP config, and the operator's credential directories.
Never a region that contains something this lane has to write.

What keeps a sibling lane, the broker's material, and the operator's home out of
a lane's *writes* is therefore not a denial at all: it is that none of them is
the working directory and none of them is in ``allowWrite``.
:func:`decides` models both rules, asymmetrically, and
:func:`assert_settings` refuses any document in which a ``denyWrite`` entry
covers an ``allowWrite`` root — which is the exact shape that failed live.

**The only socket is this lane's.** ``allowUnixSockets`` carries exactly the one
capability socket path this lane was issued, which is what makes lane A unable
to reach lane B's channel even before lane B's secret is considered
(:mod:`.capabilities`).

Two things this module does *not* prove are stated once, here, and repeated in
the README.

Mode bits are not the boundary. The launcher does strip write permission from a
runtime directory and a lane input file, but a surviving descendant runs as the
same user and can put those bits back. What actually stops it is that the path
is outside the lane's writable set in this document, which the OS enforces
against the process rather than against the file.

This is not a process-domain claim. The policy confines the authority a lane is
launched with and the filesystem and network reach of the processes it starts.
It does not prove that a process which deliberately detaches itself — ``setsid``
from inside the lane — is destroyed when the lane ends. That is an OS
process-domain property, it is owned by PAPI-93/PAPI-95, and nothing here should
be read as evidence for it.

Finally: this policy is what a *Claude agent lane* is launched under. A legacy
argv/script lane (a gate, or a reviewer or builder configured as a script) is
launched with the narrow child environment, the trusted ``PATH``, and the
capability channel, but no ``--settings`` file and therefore no OS sandbox.
Nothing in this module should be read as a claim about those lanes.
"""
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from .errors import LaunchPolicyError

# Claude's own tools that reach the filesystem or the network without going
# through the Bash sandbox. A lane gets none of them: it reads, edits, and tests
# through sandboxed Bash, where the filesystem and network policy below applies.
OUTSIDE_SANDBOX_TOOLS = (
    "Agent",
    "Edit",
    "Glob",
    "Grep",
    "NotebookEdit",
    "Read",
    "Task",
    "WebFetch",
    "WebSearch",
    "Write",
)

# The tools a lane may keep. ``Bash`` is the sandboxed one; ``TodoWrite`` writes
# nothing outside the model's own scratch state.
SANDBOXED_TOOLS = ("Bash", "TodoWrite")

# Read-only prefixes a platform needs before an interpreter, a compiler, or a
# linker will start at all. Deliberately short, and deliberately not "/": a lane
# that needs something outside this list is a code change here.
TRUSTED_RUNTIME_READ_ROOTS = (
    "/bin",
    "/sbin",
    "/usr/bin",
    "/usr/sbin",
    "/usr/lib",
    "/usr/libexec",
    "/usr/share",
    "/usr/local/bin",
    "/usr/local/lib",
    "/usr/local/share",
    "/opt/homebrew/bin",
    "/opt/homebrew/lib",
    "/opt/homebrew/share",
    "/opt/homebrew/opt",
    "/opt/homebrew/Cellar",
    "/Library/Developer/CommandLineTools",
    "/System/Library",
    "/etc/ssl",
    "/etc/passwd",
    "/etc/localtime",
    "/dev/null",
    "/dev/urandom",
    "/dev/random",
    "/dev/zero",
    "/dev/tty",
)

# Paths that must stay denied whatever else a future read root allows. The
# operator's home is passed in; these are the ones that are the same everywhere.
ALWAYS_DENIED_READ = (
    "/etc/shadow",
    "/etc/sudoers",
    "/private/etc/shadow",
    "/private/etc/sudoers",
    "/var/root",
)

# Directories inside the operator's home that hold credentials. They carry the
# denial on their own rather than inheriting it from a blanket one, because the
# blanket denial cannot be the whole story in either direction: a real worktree
# lives under the operator's home (``~/projects/worktrees/...``) and has to be
# readable inside it, and the home cannot be denied for *writing* at all without
# taking that worktree with it. So each of these is named in ``denyRead`` — where
# it is longer than the home and therefore still denied even though a sibling
# path was reopened — and in ``denyWrite``, where an exact path denies exactly
# itself and shadows nothing the lane needs.
CREDENTIAL_HOME_SUBPATHS = (
    ".ssh",
    ".gnupg",
    ".aws",
    ".config/gh",
    ".config/git",
    ".claude",
    ".claude.json",
    ".gitconfig",
    ".netrc",
    ".npmrc",
    ".docker",
    ".kube",
    ".password-store",
    "Library/Keychains",
)

# The environment variable that stops a lane's own shells from re-exporting the
# lane's environment — including its capability secret — into a grandchild.
ENV_SCRUB_VALUE = "1"

# "This caller stated no expectation." Distinct from ``None``, which for the
# socket check means the opposite: "this lane must be allowed no socket at all".
UNCHECKED = object()

# Every key this launcher writes under ``sandbox``, by the name Claude Code
# 2.1.219 reads it under. Anything else in that object is refused: a key the
# client ignores is a key that describes a document nobody enforces, and
# ``sandbox.filesystem.enabled``, ``sandbox.network.allowAll``,
# ``sandbox.network.allowedHosts``, and a root-level ``sandbox.allowLocalBinding``
# are exactly that — they read as strict and mean nothing.
KNOWN_SANDBOX_KEYS = frozenset(
    {
        "enabled",
        "failIfUnavailable",
        "allowUnsandboxedCommands",
        "autoAllowBashIfSandboxed",
        "allowAppleEvents",
        "excludedCommands",
        "network",
        "filesystem",
    }
)

KNOWN_NETWORK_KEYS = frozenset(
    {"allowedDomains", "deniedDomains", "allowLocalBinding", "allowUnixSockets"}
)

KNOWN_FILESYSTEM_KEYS = frozenset(
    {"disabled", "allowRead", "denyRead", "allowWrite", "denyWrite"}
)

# Keys that once carried this policy and are ignored by the client, kept by name
# so a document that reintroduces one fails rather than quietly weakening.
IGNORED_SANDBOX_KEYS = (
    "sandbox.allowLocalBinding",
    "sandbox.filesystem.enabled",
    "sandbox.network.allowAll",
    "sandbox.network.allowedHosts",
)

# What :func:`assert_settings` requires of a parsed document, as
# ``(dotted path, expected value)``. Checked against the JSON that was actually
# written, not against the object that produced it. Every entry is a key Claude
# Code reads; loosening any one of them is what these are here to catch.
REQUIRED: tuple[tuple[str, object], ...] = (
    ("sandbox.enabled", True),
    ("sandbox.failIfUnavailable", True),
    ("sandbox.allowUnsandboxedCommands", False),
    ("sandbox.autoAllowBashIfSandboxed", True),
    ("sandbox.allowAppleEvents", False),
    ("sandbox.excludedCommands", []),
    ("sandbox.filesystem.disabled", False),
    ("sandbox.network.allowedDomains", []),
    ("sandbox.network.deniedDomains", ["*"]),
    ("sandbox.network.allowLocalBinding", False),
    ("permissions.additionalDirectories", []),
    ("permissions.defaultMode", "acceptEdits"),
    ("enableAllProjectMcpServers", False),
    ("enabledMcpjsonServers", []),
    ("disabledMcpjsonServers", []),
    ("hooks", {}),
)


def document(
    *,
    worktree: Path | str,
    lane_scratch: Path | str,
    home: Path | str,
    runtime: Path | str,
    socket: Path | str | None,
    writable_worktree: bool,
    operator_home: str | None,
    lane_input: Path | str | None = None,
    readable_files: Sequence[Path | str] = (),
    denied_roots: Sequence[Path | str] = (),
) -> dict[str, object]:
    """Build one lane's whole settings document.

    ``lane_scratch`` and ``home`` are this launch's own directories and the only
    two things always writable. ``runtime``, ``lane_input``, and every entry in
    ``readable_files`` — the lane's settings file and the empty MCP config —
    are readable and never writable: the child runs the shim out of its runtime
    and reads its frozen packet out of its input, and can rewrite neither.

    ``denied_roots`` is where the launcher puts its own scratch root, which is
    the parent of every lane's material. It is denied for *reading* whole, and
    the lane roots above are named back inside it, so another lane's home,
    scratch, runtime, or settings is not readable at all. It is deliberately not
    denied for writing: a write denial does not nest, so denying it would deny
    this lane's own scratch and home along with it. Those siblings stay
    unwritable because they are neither the working directory nor in
    ``allowWrite``.

    ``writable_worktree`` is the builder/reviewer difference and the only one.
    A builder's worktree is named in ``allowWrite``; a reviewer's is named in
    ``denyWrite`` by exact path, which it has to be — the worktree is the lane's
    working directory, and Claude's default write boundary would otherwise allow
    it. Neither relies on mode bits
    (:meth:`~.worktrees.WorktreeProvider.seal`) that a same-user process may
    restore.
    """
    worktree = str(Path(worktree))
    lane_scratch = str(Path(lane_scratch))
    home = str(Path(home))
    runtime = str(Path(runtime))

    read_allow = [worktree, lane_scratch, home, runtime]
    if lane_input is not None:
        read_allow.append(str(Path(lane_input)))
    read_allow.extend(str(Path(item)) for item in readable_files)
    read_allow.extend(TRUSTED_RUNTIME_READ_ROOTS)

    write_allow = [lane_scratch, home]
    if writable_worktree:
        write_allow.append(worktree)

    # Reads: broad regions denied, this lane's paths named back inside them.
    deny = list(ALWAYS_DENIED_READ)
    deny.extend(str(Path(item)) for item in denied_roots)
    if operator_home:
        parent = str(Path(operator_home))
        deny.append(parent)
        deny.extend(str(Path(parent) / item) for item in CREDENTIAL_HOME_SUBPATHS)
    deny = _unique(deny)

    # Writes: exact immutable paths only. Not the operator's home, and not the
    # launcher's scratch root — a write denial does not nest, so either one would
    # take this lane's own writable roots down with it, which is what a live
    # probe of Claude Code 2.1.219 showed it doing.
    #
    # A worktree's Git metadata is not inside its checkout — a linked worktree
    # keeps its index and refs in the source clone — but the pointer file and any
    # per-worktree config that lives in the checkout are, and neither is
    # something any lane may rewrite. A reviewer's whole worktree is named for
    # the same reason: it is the lane's working directory, and Claude's own
    # default would allow writes there if nothing said otherwise.
    write_deny = [str(Path(worktree) / ".git"), runtime]
    if not writable_worktree:
        write_deny.append(worktree)
    if lane_input is not None:
        write_deny.append(str(Path(lane_input)))
    write_deny.extend(str(Path(item)) for item in readable_files)
    write_deny.extend(ALWAYS_DENIED_READ)
    if operator_home:
        parent = str(Path(operator_home))
        write_deny.extend(
            str(Path(parent) / item) for item in CREDENTIAL_HOME_SUBPATHS
        )
    write_deny = _unique(write_deny)
    _assert_writes_are_reachable(write_allow, write_deny)

    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": True,
            "allowAppleEvents": False,
            "excludedCommands": [],
            "network": {
                "allowedDomains": [],
                "deniedDomains": ["*"],
                "allowLocalBinding": False,
                "allowUnixSockets": [str(Path(socket))] if socket is not None else [],
            },
            "filesystem": {
                "disabled": False,
                "allowRead": _unique(read_allow),
                "denyRead": deny,
                "allowWrite": _unique(write_allow),
                "denyWrite": write_deny,
            },
        },
        "permissions": {
            "defaultMode": "acceptEdits",
            "additionalDirectories": [],
            "allow": [],
            "ask": [],
            "deny": [f"{tool}" for tool in OUTSIDE_SANDBOX_TOOLS],
        },
        "enableAllProjectMcpServers": False,
        "enabledMcpjsonServers": [],
        "disabledMcpjsonServers": [],
        "hooks": {},
        "includeCoAuthoredBy": False,
    }


def write(path: Path, settings: Mapping[str, object]) -> Path:
    """Write a settings document to a fresh launcher-owned file and prove it."""
    path = Path(path)
    if path.exists():
        raise LaunchPolicyError(
            "a lane's sandbox settings file already exists; every launch writes a "
            "fresh one, so an existing path is somebody else's file",
            evidence={"path": str(path)},
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    assert_settings(json.loads(path.read_text(encoding="utf-8")), source=str(path))
    return path


def decides(settings: Mapping[str, object], path: Path | str, *, write: bool) -> bool:
    """True when this document lets a lane reach ``path``. Both rules, in one place.

    Reads and writes are resolved differently, because Claude Code resolves them
    differently and a symmetric model is what produced a policy that denied a
    builder its own worktree.

    **Read.** The longest matching root wins and a tie goes to the denial. That
    is what lets a policy say "none of the launcher's scratch root, except this
    lane's directories inside it" and "none of the operator's home, except the one
    worktree this lane was authorised for" without either allowance leaking to a
    sibling: a sibling matches only the broad denial.

    **Write.** Any matching denial wins outright, however specific the allowance
    inside it, and a path with no matching allowance is denied. Nesting an
    ``allowWrite`` inside a ``denyWrite`` region buys nothing, so this function
    never pretends it does — and :func:`assert_settings` refuses a document that
    tries.

    The one thing this cannot see is Claude's own default: the working directory
    is writable unless something denies it. Every document this module builds
    names the worktree explicitly — in ``allowWrite`` for a builder, in
    ``denyWrite`` for a reviewer — precisely so that the answer here is the answer
    the OS will give.
    """
    if write:
        allow = _string_list(settings, "sandbox.filesystem.allowWrite", "decision")
        deny = _string_list(settings, "sandbox.filesystem.denyWrite", "decision")
        if _longest_match(deny, path) >= 0:
            return False
        return _longest_match(allow, path) >= 0
    allow = _string_list(settings, "sandbox.filesystem.allowRead", "decision")
    deny = _string_list(settings, "sandbox.filesystem.denyRead", "decision")
    allowed = _longest_match(allow, path)
    return allowed >= 0 and allowed > _longest_match(deny, path)


def assert_settings(
    settings: object,
    *,
    source: str,
    worktree: Path | str | None = None,
    socket: Path | str | None | object = UNCHECKED,
    operator_home: str | None = None,
    writable_worktree: bool | None = None,
    lane_writable: Sequence[Path | str] = (),
    lane_readonly: Sequence[Path | str] = (),
    denied_roots: Sequence[Path | str] = (),
    foreign_paths: Sequence[Path | str] = (),
) -> None:
    """Prove a parsed settings document is the strict policy. Fails closed.

    Everything in :data:`REQUIRED` is checked unconditionally — that is the part
    of the policy no caller may opt out of, and every key in it is one the client
    reads. The remaining arguments state what *this* lane expects:

    ``socket`` distinguishes three cases on purpose: :data:`UNCHECKED` says
    nothing, ``None`` requires that no unix socket at all is allowed, and a path
    requires exactly that one.

    ``lane_writable`` are the roots this lane must be able to write — its own
    scratch and its own synthetic home. ``lane_readonly`` are the ones it must be
    able to read and must *not* be able to write: its runtime, its frozen input,
    its settings file, the empty MCP config. ``denied_roots`` and
    ``foreign_paths`` are what must be out of reach either way: the launcher's
    scratch root, and any concrete path inside it that belongs to another lane.
    """
    if not isinstance(settings, Mapping):
        raise LaunchPolicyError(
            "a lane's sandbox settings must be a JSON object", evidence={"source": source}
        )
    for dotted, expected in REQUIRED:
        found = _dig(settings, dotted)
        if found != expected:
            raise LaunchPolicyError(
                "a lane's sandbox settings do not carry this launcher's strict policy",
                evidence={"source": source, "key": dotted, "expected": expected, "found": found},
            )

    _assert_known_keys(settings, source=source)

    denied = _dig(settings, "permissions.deny")
    if not isinstance(denied, list):
        raise LaunchPolicyError(
            "a lane's sandbox settings must deny the tools that reach outside the "
            "Bash sandbox",
            evidence={"source": source, "permissions.deny": denied},
        )
    missing = [tool for tool in OUTSIDE_SANDBOX_TOOLS if tool not in denied]
    if missing:
        raise LaunchPolicyError(
            "a lane's sandbox settings leave a built-in file or network tool available; "
            "a lane edits and tests through sandboxed Bash and nothing else",
            evidence={"source": source, "missing": missing},
        )

    read_allow = _string_list(settings, "sandbox.filesystem.allowRead", source)
    write_allow = _string_list(settings, "sandbox.filesystem.allowWrite", source)
    deny_read = _string_list(settings, "sandbox.filesystem.denyRead", source)
    deny_write = _string_list(settings, "sandbox.filesystem.denyWrite", source)
    for name, roots in (("allowRead", read_allow), ("allowWrite", write_allow)):
        for root in roots:
            if root in ("/", "", "*", "**"):
                raise LaunchPolicyError(
                    "a lane's sandbox settings allow the whole filesystem",
                    evidence={"source": source, "key": name, "root": root},
                )

    sockets = _string_list(settings, "sandbox.network.allowUnixSockets", source)
    if len(sockets) > 1:
        raise LaunchPolicyError(
            "a lane's sandbox settings allow more than one unix socket; a lane reaches "
            "its own capability channel and nothing else",
            evidence={"source": source, "found": sockets},
        )
    if socket is not UNCHECKED:
        if socket is not None:
            wanted = str(Path(socket))  # type: ignore[arg-type]
            if sockets != [wanted]:
                raise LaunchPolicyError(
                    "a lane's sandbox settings must allow exactly this lane's capability "
                    "socket and no other, so one lane cannot connect to another's channel",
                    evidence={"source": source, "expected": [wanted], "found": sockets},
                )
        elif sockets:
            raise LaunchPolicyError(
                "a lane with no capability channel must be allowed no unix socket at all",
                evidence={"source": source, "found": sockets},
            )

    tree = str(Path(worktree)) if worktree is not None else None
    if operator_home:
        _assert_operator_home(
            settings,
            source=source,
            operator_home=operator_home,
            worktree=tree,
            read_allow=read_allow,
            write_allow=write_allow,
            deny_read=deny_read,
            deny_write=deny_write,
        )

    for root in denied_roots:
        text = str(Path(root))
        if text not in deny_read:
            raise LaunchPolicyError(
                "a lane's sandbox settings do not deny reads of the launcher's own "
                "scratch root, which holds every other lane's home, runtime, and policy",
                evidence={"source": source, "key": "denyRead", "root": text},
            )
        if text in deny_write:
            raise LaunchPolicyError(
                "a lane's sandbox settings deny writes to the launcher's whole scratch "
                "root. That root contains this lane's own scratch and synthetic home, "
                "and a write denial is not reopened by a nested allowance, so the lane "
                "would be refused the two directories it exists to write. A sibling "
                "lane is kept out of writes by being neither the working directory nor "
                "an allowWrite root, not by a denial",
                evidence={"source": source, "key": "denyWrite", "root": text},
            )

    # After the two named broad roots above, so their own wording explains the
    # live failure rather than this general one catching it first.
    _assert_writes_are_reachable(write_allow, deny_write, source=source)

    for path in foreign_paths:
        for mode in (False, True):
            if decides(settings, path, write=mode):
                raise LaunchPolicyError(
                    "a lane's sandbox settings reach material that is not this lane's; "
                    "one lane may not read or write another lane's home, scratch, "
                    "runtime, settings, or the launcher's own broker material",
                    evidence={
                        "source": source,
                        "path": str(Path(path)),
                        "access": "write" if mode else "read",
                    },
                )

    for root in lane_writable:
        for mode in (False, True):
            if not decides(settings, root, write=mode):
                raise LaunchPolicyError(
                    "a lane cannot reach its own scratch or synthetic home; the lane's "
                    "own two writable directories are what replace the launcher-wide "
                    "scratch this policy no longer allows",
                    evidence={
                        "source": source,
                        "root": str(Path(root)),
                        "access": "write" if mode else "read",
                    },
                )

    for root in lane_readonly:
        if not decides(settings, root, write=False):
            raise LaunchPolicyError(
                "a lane cannot read material it is launched with",
                evidence={"source": source, "root": str(Path(root))},
            )
        if decides(settings, root, write=True):
            raise LaunchPolicyError(
                "a lane can write its own runtime, frozen input, or policy material; "
                "mode bits do not keep a same-user process out, so this has to be a "
                "path the sandbox refuses",
                evidence={"source": source, "root": str(Path(root))},
            )

    if tree is not None:
        if tree not in read_allow:
            raise LaunchPolicyError(
                "a lane must be able to read the worktree it was launched in",
                evidence={"source": source, "worktree": tree},
            )
        if not decides(settings, tree, write=False):
            raise LaunchPolicyError(
                "a lane's sandbox settings deny the worktree it was launched in; a "
                "worktree under a denied root has to be allowed back by exact path",
                evidence={"source": source, "worktree": tree},
            )
        # The worktree is the lane's working directory, which Claude makes
        # writable unless the document says otherwise. Silence here is not a
        # policy, so the document has to name it on one side or the other.
        if tree not in write_allow and tree not in deny_write:
            raise LaunchPolicyError(
                "a lane's sandbox settings say nothing about writing to the worktree. "
                "It is the lane's working directory, which this client makes writable "
                "by default, so a reviewer's worktree has to be denied by exact path "
                "rather than merely left out of the allowances",
                evidence={"source": source, "worktree": tree},
            )
        writable = tree in write_allow and decides(settings, tree, write=True)
        if writable_worktree is not None and writable != writable_worktree:
            raise LaunchPolicyError(
                "a lane's sandbox settings disagree with its role about whether the "
                "worktree is writable",
                evidence={
                    "source": source,
                    "worktree": tree,
                    "writable": writable,
                    "expected_writable": writable_worktree,
                },
            )
        metadata = str(Path(tree) / ".git")
        if metadata not in deny_write:
            raise LaunchPolicyError(
                "a lane's sandbox settings do not deny writes to the worktree's Git metadata",
                evidence={"source": source, "git_dir": metadata},
            )


def read_and_assert(path: Path, **checks: object) -> dict[str, object]:
    """Re-read a settings file from disk and prove it, immediately before spawn."""
    path = Path(path)
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LaunchPolicyError(
            "a lane's sandbox settings file could not be re-read before launch",
            evidence={"path": str(path), "error": str(exc)},
        ) from exc
    assert_settings(parsed, source=str(path), **checks)  # type: ignore[arg-type]
    return parsed


def _assert_writes_are_reachable(
    write_allow: Sequence[str], write_deny: Sequence[str], *, source: str = "generated"
) -> None:
    """No write denial may cover a path this lane has to write. Fails closed.

    The invariant that was missing. A ``denyWrite`` region is absolute in Claude
    Code — a nested ``allowWrite`` does not reopen it — so a document that names
    both is a document in which the allowance is a comment. Building one is a bug
    here, not a policy, and it is caught where it is built as well as where it is
    proved.
    """
    for root in write_allow:
        covering = [entry for entry in write_deny if _longest_match([entry], root) >= 0]
        if covering:
            raise LaunchPolicyError(
                "a lane's sandbox settings deny writes to a region containing a path "
                "the lane must write; a write denial is absolute in this client and a "
                "nested allowance does not reopen it, so this policy would refuse the "
                "lane its own worktree, scratch, or home",
                evidence={"source": source, "allowWrite": root, "denyWrite": covering},
            )


def _assert_known_keys(settings: Mapping[str, object], *, source: str) -> None:
    """Every key under ``sandbox`` must be one Claude Code actually reads."""
    for dotted in IGNORED_SANDBOX_KEYS:
        if _dig(settings, dotted) is not None:
            raise LaunchPolicyError(
                "a lane's sandbox settings carry a key this client ignores; a setting "
                "that reads as strict and is never enforced is worse than none",
                evidence={"source": source, "key": dotted, "ignored": list(IGNORED_SANDBOX_KEYS)},
            )
    for dotted, known in (
        ("sandbox", KNOWN_SANDBOX_KEYS),
        ("sandbox.network", KNOWN_NETWORK_KEYS),
        ("sandbox.filesystem", KNOWN_FILESYSTEM_KEYS),
    ):
        section = _dig(settings, dotted)
        if not isinstance(section, Mapping):
            raise LaunchPolicyError(
                "a lane's sandbox settings are missing a section this policy owns",
                evidence={"source": source, "key": dotted},
            )
        unknown = sorted(set(section) - known)
        if unknown:
            raise LaunchPolicyError(
                "a lane's sandbox settings carry a key outside the documented set; an "
                "unrecognised key is not a policy, it is decoration",
                evidence={"source": source, "key": dotted, "unknown": unknown},
            )


def _assert_operator_home(
    settings: Mapping[str, object],
    *,
    source: str,
    operator_home: str,
    worktree: str | None,
    read_allow: list[str],
    write_allow: list[str],
    deny_read: list[str],
    deny_write: list[str],
) -> None:
    """The operator's home is denied whole; only the authorised worktree returns.

    A real lane worktree lives under ``~/projects/worktrees``, so a policy that
    refused every allowed root inside the operator's home refused every real
    run. What has to hold instead is narrower and checkable: the home is denied,
    the only root allowed back inside it is the exact worktree this lane was
    authorised for, and every credential directory stays denied whichever way
    the lists are read.
    """
    parent = str(Path(operator_home))
    if parent in deny_write:
        raise LaunchPolicyError(
            "a lane's sandbox settings deny writes to the operator's whole home "
            "directory. A real worktree lives under that home, and a write denial is "
            "not reopened by a nested allowance, so this refuses the builder the "
            "worktree it was launched to fix. The home is denied for reading; what "
            "keeps writes out of it is that nothing else under it is the working "
            "directory or an allowWrite root, plus the exact credential denials below",
            evidence={"source": source, "key": "denyWrite", "home": parent},
        )
    if worktree is not None:
        for relative in CREDENTIAL_HOME_SUBPATHS:
            credential = str(Path(parent) / relative)
            if worktree == credential or _within(credential, worktree):
                raise LaunchPolicyError(
                    "this lane's worktree is a credential directory in the operator's "
                    "home; the worktree is the one path allowed back inside that home, "
                    "so it may not be one of the paths the home is denied for",
                    evidence={"source": source, "worktree": worktree, "credential": credential},
                )
    if parent not in deny_read:
        raise LaunchPolicyError(
            "a lane's sandbox settings do not deny reads of the operator's home directory",
            evidence={"source": source, "key": "denyRead", "home": parent},
        )
    for name, roots in (("allowRead", read_allow), ("allowWrite", write_allow)):
        for root in roots:
            if root != parent and not _within(parent, root):
                continue
            if worktree is not None and root == worktree:
                continue
            raise LaunchPolicyError(
                "a lane's sandbox settings allow a path inside the operator's home that "
                "is not this lane's authorised worktree",
                evidence={
                    "source": source,
                    "key": name,
                    "home": parent,
                    "root": root,
                    "worktree": worktree,
                },
            )
    for relative in CREDENTIAL_HOME_SUBPATHS:
        credential = str(Path(parent) / relative)
        if credential not in deny_write:
            raise LaunchPolicyError(
                "a lane's sandbox settings do not deny writes to a credential directory "
                "in the operator's home by exact path; the home itself cannot carry that "
                "denial for writes, so each of these has to",
                evidence={"source": source, "key": "denyWrite", "path": credential},
            )
        for mode in (False, True):
            if decides(settings, credential, write=mode):
                raise LaunchPolicyError(
                    "a lane's sandbox settings reach a credential directory in the "
                    "operator's home",
                    evidence={
                        "source": source,
                        "path": credential,
                        "access": "write" if mode else "read",
                    },
                )


def _dig(settings: Mapping[str, object], dotted: str) -> object:
    current: object = settings
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _string_list(settings: Mapping[str, object], dotted: str, source: str) -> list[str]:
    found = _dig(settings, dotted)
    if not isinstance(found, list) or any(not isinstance(item, str) for item in found):
        raise LaunchPolicyError(
            "a lane's sandbox settings key must be a list of paths",
            evidence={"source": source, "key": dotted, "found": found},
        )
    return [str(item) for item in found]


def _longest_match(roots: Iterable[str], path: Path | str) -> int:
    """Length of the most specific root covering ``path``, or ``-1`` for none."""
    text = str(Path(path))
    best = -1
    for root in roots:
        if not root:
            continue
        normalised = str(Path(root))
        if text == normalised or text.startswith(normalised.rstrip("/") + "/"):
            best = max(best, len(normalised))
    return best


def _within(parent: str, candidate: str) -> bool:
    try:
        Path(candidate).relative_to(Path(parent))
    except ValueError:
        return False
    return True


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


__all__ = [
    "ALWAYS_DENIED_READ",
    "UNCHECKED",
    "CREDENTIAL_HOME_SUBPATHS",
    "ENV_SCRUB_VALUE",
    "IGNORED_SANDBOX_KEYS",
    "KNOWN_FILESYSTEM_KEYS",
    "KNOWN_NETWORK_KEYS",
    "KNOWN_SANDBOX_KEYS",
    "OUTSIDE_SANDBOX_TOOLS",
    "REQUIRED",
    "SANDBOXED_TOOLS",
    "TRUSTED_RUNTIME_READ_ROOTS",
    "assert_settings",
    "decides",
    "document",
    "read_and_assert",
    "write",
]
