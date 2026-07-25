"""The hardened launchers: the only place a child gets an environment.

Every lane the loop runs — a baseline gate, a reviewer, the builder — is
launched through :class:`LaunchBroker`. The broker builds the child's
environment from nothing (:mod:`.childenv`), opens the one narrow capability
channel that lane is entitled to (:mod:`.capabilities`), and, for an agent lane,
builds the whole argv array itself from a code-owned prompt (:mod:`.prompts`).

Launch discipline lives here as code rather than as instructions somebody
remembers to follow:

**No credential in any child.** A lane is never handed a GitHub token under any
name. It gets the path of a launcher-owned unix socket and a shim on its
``PATH``; the launcher, on the other side of that socket, performs exactly
``push-branch``, ``comment-pr``, and ``review-pr`` against the bound repository,
pull request, branch, and head. A child cannot merge, cannot push another ref or
another repository, and cannot approve a review, because none of those is an
operation it can name.

**A synthetic HOME, and a lane-scoped scratch.** No child inherits the
operator's home directory. Every launch gets a directory of its own under the
launcher's scratch root, and inside it a synthetic home, a writable scratch
(which is also the lane's ``TMPDIR``), a read-only runtime, a read-only input
directory for whatever frozen material the lane was pointed at, and its own
settings file. Every configuration-discovery variable this module knows about —
``GH_CONFIG_DIR``, ``GIT_CONFIG_GLOBAL``/``GIT_CONFIG_SYSTEM``,
``CLAUDE_CONFIG_DIR``, ``GNUPGHOME``, and the four XDG directories — points
inside that home. Only material named in :data:`REVIEWED_HOME_MATERIAL` is
copied in, and that list is empty: adding to it is a code change, not a
configuration one.

The launcher's scratch *root* is not a lane's to touch. It holds every lane's
home, runtime, and settings file, the empty MCP config, and the capability
broker's own material, and a lane that could write there could hand the next
lane a different program or a different policy. So the sandbox denies the root
whole and allows exactly this lane's two writable directories back inside it.

**Empty MCP.** Every agent lane is launched with ``--strict-mcp-config`` and an
``--mcp-config`` file this module wrote containing no servers, so a project or
user MCP configuration cannot attach tools to a child.

**A launcher-owned strict sandbox.** Every Claude agent lane is launched with a
settings file this module generated for that one launch (:mod:`.sandbox`),
passed as ``--settings``, alongside a launcher-owned ``--setting-sources`` entry
that names no source at all — so neither the operator's settings, nor the
settings a *pull request under review* could add to its own ``.claude``
directory, are read. The document turns the OS sandbox on, makes an unavailable
sandbox fatal, forbids unsandboxed commands, enumerates the lane's readable and
writable paths, denies the operator's home and credential directories and the
launcher's own scratch root, allows no outbound domain and exactly one unix
socket — this lane's capability channel — and denies every built-in tool that
reaches the filesystem or the network outside the Bash sandbox. It is re-read
from disk and proved again immediately before the spawn. A configuration cannot
supply, replace, or add to it: both flags are refused from any other source.

That sandbox is what a *Claude agent lane* runs under. A gate, and a reviewer or
builder configured as an argv/script lane, get the narrow child environment, the
trusted ``PATH``, the lane-scoped home and scratch, and the capability channel —
but no ``--settings`` file, because they are not launched through the Claude
client at all. They are not OS-sandboxed, and this module does not claim they
are.

**Bounded tools.** The tool set is a code-owned maximum per role, and a
configuration may only narrow it. Since a lane edits and tests through sandboxed
Bash, that maximum is now ``Bash`` and ``TodoWrite`` for both roles: ``Read``,
``Edit``, ``Write``, ``Glob``, ``Grep``, ``WebFetch``, and ``WebSearch`` operate
outside the Bash sandbox, so a lane is given none of them, on argv and in the
settings document alike.

**A fresh runtime, and a ``PATH`` that is not the operator's.** Every launch
gets its own runtime directory with its own copy of the capability shim
(:mod:`.runtime`). Its write bits are stripped, but that is the second lock, not
the first: a same-user descendant can put mode bits back, so what actually keeps
a lane out of its own runtime — and out of every other lane's — is that the
sandbox document does not list it as writable. The child's ``PATH`` is that directory
followed by a short list of trusted system directories and nothing else, so no
lane inherits the operator's ``PATH`` or sees another lane's runtime. Every
configured program is resolved to an absolute path and fingerprinted before the
launch and re-checked immediately before the spawn.

**Bounded budget.** An agent lane runs against a wall-clock budget between 20
and 30 minutes. Outside that window the run stops rather than clamping quietly:
a lane given four hours is a different risk from the one that was reviewed.

**Quiet stdout.** Children are captured, never inherited, with progress
rendering turned off by environment and whatever escape sequences and carriage
-return rewrites survive stripped from the captured stream before anything
parses it. A spinner frame must not be able to hide, or forge, the final line.

**One final marker.** The prompts state the exact marker, and
:mod:`.verdicts` — unchanged — is what reads it. Nothing here interprets a
lane's claims.

Three refusals are worth naming. A caller may not pass an environment into
:meth:`LaunchBroker.run_gate` and friends: an environment assembled anywhere
else is exactly the runtime override that would put the authority back. A
composed agent argv is re-scanned for authority-broadening flags before launch,
so a future edit that threads ``--dangerously-skip-permissions`` or
``--add-dir`` in from configuration fails closed instead of shipping. And a
reviewer or builder lane without a scoped identity is refused outright, script
lane or agent lane alike — a lane with nothing to act as has nothing to prove
afterwards.

Nothing here trusts a child's own account of what it did. The broker proves
which account a credential is *before* the launch; the loop proves what landed
on GitHub *after* it.

**One limitation, stated plainly.** All of the above confines the authority a
lane is *launched with* and the filesystem, network, and GitHub reach of the
processes it starts. None of it proves that a process which deliberately
detaches itself from the lane's process group — a self-``setsid`` descendant —
is destroyed when the lane ends. :class:`~.commands.SubprocessRunner` tears down
the group it created, and that is the group, not the OS process domain. Proving
destruction of a deliberately detached descendant is a separate piece of work,
owned by PAPI-93/PAPI-95. Nothing in this module should be read as evidence for
it.
"""
from __future__ import annotations

import json
import re
import shutil
import stat
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .capabilities import (
    SHIM_NAME,
    CapabilityBroker,
    CapabilityChannel,
    CapabilityScope,
)
from .childenv import (
    CAPABILITY_CHANNEL,
    CAPABILITY_SECRET,
    CLAUDE_TMPDIR,
    HOME_GUARDS,
    SUBPROCESS_ENV_SCRUB,
    EnvironmentPolicy,
)
from .commands import CommandResult, CommandRunner, validate_argv
from .errors import LaunchPolicyError
from .identities import (
    BUILDER_CAPABILITIES,
    REVIEWER_CAPABILITIES,
    IdentitySpec,
    IdentityVerifier,
    ResolvedIdentity,
    assert_scope,
    resolve,
)
from .prompts import builder_prompt, reviewer_prompt
from .runtime import LaneRuntime, TrustedProgram, resolution_path, resolve_program
from .sandbox import ENV_SCRUB_VALUE, SANDBOXED_TOOLS
from .sandbox import document as sandbox_document
from .sandbox import read_and_assert as assert_sandbox_file
from .sandbox import write as write_sandbox_settings

# The 20-30 minute background budget, in seconds, and the default inside it.
BUDGET_MIN = 1200.0
BUDGET_MAX = 1800.0
DEFAULT_BUDGET = 1500.0

# Code-owned tool maxima. A configuration may narrow these; it can never widen
# them.
#
# Both roles get the same set, and it is small, because the boundary moved: a
# lane's authority over files and the network is now the OS sandbox
# (:mod:`.sandbox`), and the only tool that runs *inside* that sandbox is
# ``Bash``. ``Read``, ``Edit``, ``Write``, ``Glob``, ``Grep``, ``WebFetch``, and
# ``WebSearch`` are the model client's own implementations and are not subject to
# it, so a lane that kept ``Read`` could read the operator's home however tightly
# the sandbox were drawn. A lane reads, edits, and tests through sandboxed Bash.
# ``TodoWrite`` touches only the model's own scratch state.
#
# What keeps a reviewer read-only is therefore no longer the absence of an edit
# tool: it is the sandbox's write policy, which does not include the reviewer's
# worktree, plus the exact-tree check the loop runs afterwards.
BUILDER_TOOLS = SANDBOXED_TOOLS
REVIEWER_TOOLS = SANDBOXED_TOOLS

# Permission modes a child may run under. "bypassPermissions" and "auto" are
# absent on purpose: both dissolve the tool boundary the allowlist just drew.
PERMISSION_MODES = ("acceptEdits", "dontAsk", "manual", "plan")

# What may be copied from the operator's home into a synthetic one, as paths
# relative to both. Empty, and meant to stay that way: every candidate is a file
# somebody has to read and certify carries no credential and no client data.
# Widening this is a code change that shows up in review, not a config key.
REVIEWED_HOME_MATERIAL: tuple[str, ...] = ()

# Flags that would widen a child's authority past what this module grants,
# whatever composed them.
FORBIDDEN_FLAGS = (
    "--add-dir",
    "--agents",
    "--allow-dangerously-skip-permissions",
    "--chrome",
    "--continue",
    "--dangerously-skip-permissions",
    "--from-pr",
    "--ide",
    "--plugin-dir",
    "--plugin-url",
    "--remote-control",
    "--resume",
    "--settings",
    "--setting-sources",
    "--system-prompt",
)

# The launcher's own ``--setting-sources`` argv entry. The single-token form
# carries an empty list, which is the whole point: no user, project, or local
# settings source is consulted, so neither the operator's configuration nor a
# ``.claude`` directory committed by the pull request under review can add to
# the document this module wrote.
SETTING_SOURCES_ENTRY = "--setting-sources="

_EMPTY_MCP = {"mcpServers": {}}
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
_SLUG = re.compile(r"[^a-z0-9_-]+")
_FALLBACK_PATH = "/usr/bin:/bin"


@dataclass(frozen=True)
class AgentSpec:
    """How to launch one agent lane. Everything else about the launch is code-owned."""

    program: str
    model: str
    tools: tuple[str, ...]
    permission_mode: str = "acceptEdits"


@dataclass(frozen=True)
class BoundContext:
    """The exact repository, pull request, branch, and commit a lane is bound to."""

    repo: str
    pr: int
    branch: str
    base: str
    head: str

    def env(self) -> dict[str, str]:
        return {
            "PR_PROVER_REPO": self.repo,
            "PR_PROVER_PR": str(self.pr),
            "PR_PROVER_BRANCH": self.branch,
            "PR_PROVER_BASE": self.base,
            "PR_PROVER_HEAD": self.head,
        }

    def scope(self) -> CapabilityScope:
        return CapabilityScope(repo=self.repo, pr=self.pr, branch=self.branch, head=self.head)


def quiet(text: str) -> str:
    """Strip progress rendering from a captured stream without touching content.

    Escape sequences go, carriage-return rewrites collapse to the frame that
    actually survived, trailing whitespace goes, and runs of blank lines become
    one. Line content is otherwise untouched, so a marker line reaches the
    parser byte for byte.
    """
    if not text:
        return ""
    cleaned: list[str] = []
    blank = False
    for raw in _ANSI.sub("", text).split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        if "\r" in line:
            line = line.rsplit("\r", 1)[-1]
        line = line.rstrip()
        if not line:
            if blank:
                continue
            blank = True
        else:
            blank = False
        cleaned.append(line)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return "\n".join(cleaned) + ("\n" if cleaned else "")


def assert_launchable(
    argv: Sequence[str],
    *,
    settings: Path | str | None = None,
    setting_sources: bool = False,
) -> tuple[str, ...]:
    """Reject an argv array that would broaden a child's authority.

    ``--settings`` and ``--setting-sources`` are forbidden like every other
    authority-widening flag, with one exception each: the entries *this module*
    composed for a Claude agent lane. ``settings`` is the exact path this
    launcher just wrote, and it must appear exactly once, in the two-token form,
    with that exact path as its value. ``setting_sources`` permits exactly one
    :data:`SETTING_SOURCES_ENTRY` token and nothing that merely looks like it.

    So a configuration cannot supply either flag, cannot replace the launcher's
    settings file with one of its own, and cannot append a second occurrence
    that a later parse might prefer.
    """
    checked = validate_argv(argv, what="child launch")
    wanted_settings = str(Path(settings)) if settings is not None else None
    seen_settings = 0
    seen_sources = 0
    for index, item in enumerate(checked):
        flag = item.split("=", 1)[0]
        if flag not in FORBIDDEN_FLAGS:
            continue
        if flag == "--settings" and wanted_settings is not None:
            value = checked[index + 1] if index + 1 < len(checked) else None
            if item == "--settings" and value == wanted_settings:
                seen_settings += 1
                continue
        if flag == "--setting-sources" and setting_sources and item == SETTING_SOURCES_ENTRY:
            seen_sources += 1
            continue
        raise LaunchPolicyError(
            "this launch would give the child authority the launcher does not own",
            evidence={"flag": flag, "index": index, "forbidden": list(FORBIDDEN_FLAGS)},
        )
    if wanted_settings is not None and seen_settings != 1:
        raise LaunchPolicyError(
            "an agent lane must carry exactly one launcher-owned --settings entry",
            evidence={"settings": wanted_settings, "occurrences": seen_settings},
        )
    if setting_sources and seen_sources != 1:
        raise LaunchPolicyError(
            "an agent lane must carry exactly one launcher-owned --setting-sources entry",
            evidence={"entry": SETTING_SOURCES_ENTRY, "occurrences": seen_sources},
        )
    return checked


@dataclass(frozen=True)
class LaneMaterial:
    """Everything one launch owns on disk, and nothing any other launch owns.

    ``directory`` is this launch's own subtree of the launcher's scratch root.
    ``scratch`` and the synthetic home inside ``home`` are the only two things
    the lane may write; ``tmp`` is the lane's ``TMPDIR`` and lives inside its
    scratch, so a temporary file never lands in a directory another lane shares.
    ``runtime``, ``inputs``, and ``settings`` are the lane's to read and nobody's
    to write.
    """

    slug: str
    home: Mapping[str, str]
    runtime: LaneRuntime
    directory: Path
    scratch: Path
    tmp: Path
    inputs: Path
    settings: Path

    @property
    def home_directory(self) -> str:
        return self.home["HOME"]

    @property
    def readonly_roots(self) -> tuple[Path, ...]:
        """What this lane reads and may never write."""
        return (self.runtime.directory, self.inputs, self.settings)

    @property
    def writable_roots(self) -> tuple[Path, ...]:
        """The lane's own two writable directories, and the only two."""
        return (self.scratch, Path(self.home_directory))


class LaunchBroker:
    """The one credential broker. Builds every child environment and agent argv."""

    def __init__(
        self,
        *,
        runner: CommandRunner,
        policy: EnvironmentPolicy,
        identities: Mapping[str, IdentitySpec] | None = None,
        verifier: IdentityVerifier | None = None,
        parent_env: Mapping[str, str] | None = None,
        worktree_root: Path | None = None,
        scratch_root: Path | None = None,
        on_event: Callable[[str], None] | None = None,
    ) -> None:
        self._runner = runner
        self._policy = policy
        self._identities = dict(identities or {})
        self._verifier = verifier
        self._parent_env = dict(parent_env if parent_env is not None else {})
        self._worktree_root = Path(worktree_root).resolve() if worktree_root else None
        self._scratch_root = Path(scratch_root) if scratch_root else None
        self._on_event = on_event
        self._scratch: Path | None = None
        self._resolved: dict[str, ResolvedIdentity] = {}
        self._verified: set[str] = set()
        self._open_channels: list[CapabilityChannel] = []
        self.channels: list[CapabilityChannel] = []
        # Every launch gets its own runtime directory, numbered so two lanes with
        # the same slug can never be handed the same path.
        self._runtimes: list[LaneRuntime] = []
        self._launches = 0
        # Channel closures that could not account for their handlers. The loop
        # turns these into a fail-closed stop rather than reporting a run whose
        # brokered work is unaccounted for.
        self.shutdown_errors: list[LaunchPolicyError] = []

    # -- lanes -------------------------------------------------------------
    def run_gate(
        self, *, name: str, argv: Sequence[str], cwd: Path, timeout: float | None
    ) -> CommandResult:
        """Run a repository gate with no GitHub identity and no capability channel."""
        lane = f"gate {name}"
        self._assert_isolated(cwd, lane=lane)
        material = self._material(lane, identity=None)
        env = self._environment(
            cwd=cwd, bound=None, lane=lane, channel=None, material=material
        )
        argv, program = self._script_argv(argv, lane=lane, cwd=cwd)
        return self._launch(
            argv, cwd=cwd, env=env, timeout=timeout, material=material, programs=(program,)
        )

    def run_reviewer(
        self,
        *,
        role: str,
        identity: str | None,
        agent: AgentSpec | None,
        argv: Sequence[str] | None,
        bound: BoundContext,
        cwd: Path,
        timeout: float | None,
    ) -> CommandResult:
        """Run one fresh reviewer lane against the exact head."""
        lane = f"reviewer {role}"
        self._assert_isolated(cwd, lane=lane)
        resolved = self._identity_for(lane, identity, required=REVIEWER_CAPABILITIES)
        self._verify(resolved, lane=lane, repo=bound.repo)
        with self._channel(lane=lane, identity=resolved, bound=bound, cwd=cwd) as channel:
            material = self._material(lane, identity=resolved)
            env = self._environment(
                identity=resolved,
                cwd=cwd,
                bound=bound,
                lane=lane,
                channel=channel,
                material=material,
                agent=agent is not None,
                extra={"PR_PROVER_ROLE": role},
            )
            if agent is None:
                checked, program = self._script_argv(
                    _required(argv, lane=lane), lane=lane, cwd=cwd
                )
                return self._launch(
                    checked,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                    material=material,
                    programs=(program,),
                )
            prompt = reviewer_prompt(
                repo=bound.repo,
                pr=bound.pr,
                branch=bound.branch,
                head=bound.head,
                worktree=str(cwd),
                login=resolved.login,
                role=role,
            )
            return self._launch_agent(
                agent,
                prompt=prompt,
                cwd=cwd,
                env=env,
                timeout=timeout,
                lane=lane,
                material=material,
                channel=channel,
                writable_worktree=False,
            )

    def run_builder(
        self,
        *,
        identity: str | None,
        agent: AgentSpec | None,
        argv: Sequence[str] | None,
        bound: BoundContext,
        cwd: Path,
        timeout: float | None,
        attempt: int,
        mode: str,
        blockers_file: Path,
        signature: str,
    ) -> CommandResult:
        """Run the direct-write fix lane against the bound branch."""
        lane = f"builder ({mode})"
        self._assert_isolated(cwd, lane=lane)
        resolved = self._identity_for(lane, identity, required=BUILDER_CAPABILITIES)
        self._verify(resolved, lane=lane, repo=bound.repo)
        with self._channel(lane=lane, identity=resolved, bound=bound, cwd=cwd) as channel:
            material = self._material(lane, identity=resolved)
            # Not the run's own copy: that lives beside every other attempt's
            # packet in the run's scratch, and pointing the lane there would mean
            # allowing that whole directory into its sandbox.
            packet = self.lane_input(material, blockers_file, name="blockers.json")
            env = self._environment(
                identity=resolved,
                cwd=cwd,
                bound=bound,
                lane=lane,
                channel=channel,
                material=material,
                agent=agent is not None,
                extra={
                    "PR_PROVER_ATTEMPT": str(attempt),
                    "PR_PROVER_MODE": mode,
                    "PR_PROVER_BLOCKERS_FILE": str(packet),
                },
            )
            if agent is None:
                checked, program = self._script_argv(
                    _required(argv, lane=lane), lane=lane, cwd=cwd
                )
                return self._launch(
                    checked,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                    material=material,
                    programs=(program,),
                )
            prompt = builder_prompt(
                repo=bound.repo,
                pr=bound.pr,
                branch=bound.branch,
                head=bound.head,
                worktree=str(cwd),
                login=resolved.login,
                attempt=attempt,
                mode=mode,
                blockers_file=str(packet),
                signature=signature,
            )
            return self._launch_agent(
                agent,
                prompt=prompt,
                cwd=cwd,
                env=env,
                timeout=timeout,
                lane=lane,
                material=material,
                channel=channel,
                writable_worktree=True,
            )

    # -- identities --------------------------------------------------------
    def _identity_for(
        self, lane: str, name: str | None, *, required: frozenset[str]
    ) -> ResolvedIdentity:
        if name is None:
            raise LaunchPolicyError(
                "a reviewer or builder lane must be bound to one scoped identity; a lane "
                "with no identity has no capability channel and nothing to read back",
                evidence={"lane": lane, "known": sorted(self._identities)},
            )
        spec = self._identities.get(name)
        if spec is None:
            raise LaunchPolicyError(
                "this lane names an identity the launcher does not own",
                evidence={"lane": lane, "identity": name, "known": sorted(self._identities)},
            )
        if spec.capabilities != required:
            raise LaunchPolicyError(
                "this lane's identity does not carry exactly the capabilities the role allows",
                evidence={
                    "lane": lane,
                    "identity": name,
                    "declared": sorted(spec.capabilities),
                    "required": sorted(required),
                },
            )
        if name not in self._resolved:
            self._resolved[name] = resolve(spec, self._parent_env)
            self._event(f"{lane}: resolved identity {name} ({spec.login}) from {spec.source_name}")
        return self._resolved[name]

    def _verify(self, identity: ResolvedIdentity, *, lane: str, repo: str) -> None:
        """Prove the credential is this account, with no authority beyond its capabilities."""
        if identity.spec.name in self._verified:
            return
        if self._verifier is None:
            raise LaunchPolicyError(
                "a lane declares a scoped identity but no verifier is available to "
                "prove which account it is; refusing to launch on an unverified credential",
                evidence={"lane": lane, "identity": identity.spec.name},
            )
        facts = self._verifier.facts(self.broker_env(identity), repo=repo)
        assert_scope(identity, facts, repo=repo, lane=lane)
        self._verified.add(identity.spec.name)
        self._event(
            f"{lane}: credential verified as {facts.login} with "
            f"{sorted(name for name, held in facts.permissions.items() if held)} on {repo}"
        )

    def broker_env(self, identity: ResolvedIdentity) -> dict[str, str]:
        """The launcher-side environment the capability broker acts with.

        Never handed to a child. It carries the scoped credential and points
        ``gh`` and ``git`` at launcher-owned configuration rather than the
        operator's, so the broker acts as exactly this identity too.
        """
        # Launcher-side, and deliberately not under ``lanes``: no lane is
        # allowed to read this one, because the broker acts here with a real
        # credential and a lane is never given one.
        home = self._home_for(
            self._scratch_dir() / "broker" / _slug(identity.spec.name), identity=identity
        )
        return identity.broker_env(
            {
                # The broker runs launcher-side and needs to find ``git`` and
                # ``gh``, which the operator may have installed anywhere; this is
                # the one place the operator's PATH is still consulted, and it is
                # never a child's.
                "PATH": self._parent_env.get("PATH", _FALLBACK_PATH),
                "LANG": self._parent_env.get("LANG", "C"),
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_CONFIG_SYSTEM": "/dev/null",
                **{name: value for name, value in home.items() if name != "GIT_CONFIG_SYSTEM"},
            }
        )

    # -- capability channel -------------------------------------------------
    def _channel(
        self, *, lane: str, identity: ResolvedIdentity, bound: BoundContext, cwd: Path
    ) -> CapabilityChannel:
        """Open this lane's capability channel. Closed again when the lane ends."""
        broker = CapabilityBroker(
            runner=self._runner,
            scope=bound.scope(),
            capabilities=identity.spec.capabilities,
            worktree=Path(cwd),
            credential_env=self.broker_env(identity),
            scratch=self._scratch_dir(),
            on_event=self._on_event,
        )
        channel = _TrackedChannel(
            broker, label=_slug(lane), broker_owner=self, on_event=self._on_event
        )
        self._open_channels.append(channel)
        self.channels.append(channel)
        self._event(
            f"{lane}: capability channel open for {sorted(identity.spec.capabilities)} on "
            f"{bound.repo}#{bound.pr} {bound.branch}@{bound.head[:12]}"
        )
        return channel

    def _forget_channel(self, channel: CapabilityChannel) -> None:
        if channel in self._open_channels:
            self._open_channels.remove(channel)

    # -- environment -------------------------------------------------------
    def _material(self, lane: str, *, identity: ResolvedIdentity | None) -> LaneMaterial:
        """Build this one launch's own subtree. Never reused between lanes.

        Everything a lane touches on disk is created here, under one directory
        that belongs to this launch and no other: its synthetic home, its
        writable scratch and the ``TMPDIR`` inside it, its input directory, and
        its runtime. The launcher's scratch root above them is denied to the
        lane by the sandbox document, so a lane cannot walk up out of this
        directory into a sibling's.
        """
        self._launches += 1
        slug = _slug(lane)
        directory = self._scratch_dir() / "lanes" / f"{self._launches:03d}-{slug}"
        if directory.exists():  # pragma: no cover - the counter never repeats
            raise LaunchPolicyError(
                "this lane's directory already exists; every launch gets a fresh one, "
                "so an existing path is another lane's material",
                evidence={"lane": lane, "directory": str(directory)},
            )
        scratch = directory / "scratch"
        tmp = scratch / "tmp"
        inputs = directory / "input"
        for path in (directory, scratch, tmp, inputs):
            path.mkdir(parents=True, exist_ok=False)
            path.chmod(0o700)
        home = self._home_for(directory / "home", identity=identity)
        runtime = LaneRuntime(directory / "runtime", label=slug, sequence=self._launches)
        self._runtimes.append(runtime)
        return LaneMaterial(
            slug=slug,
            home=home,
            runtime=runtime,
            directory=directory,
            scratch=scratch,
            tmp=tmp,
            inputs=inputs,
            settings=directory / "settings.json",
        )

    def lane_input(self, material: LaneMaterial, source: Path, *, name: str) -> Path:
        """Copy one frozen file into this lane's read-only input directory.

        The builder's blocker packet is written into the *run's* scratch, beside
        every other attempt's packet. Handing the lane that path would mean
        allowing the run's scratch into the lane's sandbox, which is the whole
        directory of blockers for every attempt. So the launcher copies the one
        file this lane is entitled to and points the lane at the copy.
        """
        target = Path(material.inputs) / name
        shutil.copyfile(Path(source), target)
        target.chmod(0o400)
        return target

    def _environment(
        self,
        *,
        cwd: Path,
        bound: BoundContext | None,
        lane: str,
        channel: CapabilityChannel | None,
        material: LaneMaterial,
        identity: ResolvedIdentity | None = None,
        agent: bool = False,
        extra: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        inject = dict(material.home)
        # This lane's own runtime, then trusted system directories. The
        # operator's PATH is not part of it, and neither is any other lane's.
        inject["PATH"] = material.runtime.child_path()
        if channel is not None:
            inject[CAPABILITY_CHANNEL] = str(channel.path)
            # The one thing that makes the socket path mean anything. It travels
            # here and nowhere else: not on argv, not in a file the request names.
            inject[CAPABILITY_SECRET] = channel.secret
        overrides: dict[str, str] = {
            "CI": "1",
            "NO_COLOR": "1",
            "CLICOLOR": "0",
            "TERM": "dumb",
            "PAGER": "cat",
            "COLUMNS": "200",
            "GIT_TERMINAL_PROMPT": "0",
            # A reviewer worktree is marked read-only; bytecode files written
            # into it would be a mutation the run then has to explain.
            "PYTHONDONTWRITEBYTECODE": "1",
            # Inside the lane's own writable scratch. A child that writes a
            # temporary file writes it where only this lane can read it, and
            # never into a directory the launcher or another lane shares.
            #
            # Both names, because they are read by different things. ``TMPDIR``
            # is what an ordinary script lane's shell and toolchain use. A Claude
            # agent lane's sandboxed Bash ignores it — a live probe reported
            # ``TMPDIR=/tmp/claude-501`` whatever the launcher set, because the
            # client supplies its own session temporary directory — and reads
            # ``CLAUDE_CODE_TMPDIR`` instead. Setting only the first left every
            # agent lane writing temporary files into a directory shared with
            # every other lane on the machine.
            "TMPDIR": str(material.tmp),
            CLAUDE_TMPDIR: str(material.tmp),
        }
        if agent:
            # Stop the lane's own shells from re-exporting the lane's
            # environment — the capability secret above, in particular — into
            # processes further down.
            overrides[SUBPROCESS_ENV_SCRUB] = ENV_SCRUB_VALUE
        if bound is not None:
            overrides.update(bound.env())
        overrides.update(extra or {})
        overrides["PR_PROVER_LANE"] = lane
        return self._policy.build(self._parent_env, inject=inject, overrides=overrides)

    def _home_for(self, home: Path, *, identity: ResolvedIdentity | None) -> dict[str, str]:
        """Build one synthetic home and return the variables that point inside it.

        A child never sees the operator's home directory. ``gh``, ``git``,
        ``gpg``, the model client, and everything that follows the XDG
        convention are all pointed at directories this launcher made, so a
        toolchain that goes looking for stored credentials finds an empty tree
        rather than the operator's.
        """
        home = Path(home)
        home.mkdir(parents=True, exist_ok=True)
        config = home / ".config"
        gh_config = config / "gh"
        claude_config = home / ".claude"
        cache = home / ".cache"
        data = home / ".local" / "share"
        state = home / ".local" / "state"
        gnupg = home / ".gnupg"
        for directory in (config, gh_config, claude_config, cache, data, state, gnupg):
            directory.mkdir(parents=True, exist_ok=True)
            directory.chmod(0o700)
        home.chmod(0o700)
        self._copy_reviewed_material(home)
        gitconfig = home / ".gitconfig"
        gitconfig.write_text(_gitconfig(identity), encoding="utf-8")
        gitconfig.chmod(0o600)
        guards = {
            "HOME": str(home),
            "CLAUDE_CONFIG_DIR": str(claude_config),
            "GH_CONFIG_DIR": str(gh_config),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GNUPGHOME": str(gnupg),
            "XDG_CACHE_HOME": str(cache),
            "XDG_CONFIG_HOME": str(config),
            "XDG_DATA_HOME": str(data),
            "XDG_STATE_HOME": str(state),
        }
        missing = sorted(set(HOME_GUARDS) - set(guards))
        if missing:  # pragma: no cover - a build-time invariant
            raise LaunchPolicyError(
                "a synthetic home was built without every declared guard",
                evidence={"missing": missing},
            )
        return guards

    def _copy_reviewed_material(self, home: Path) -> None:
        """Copy only what :data:`REVIEWED_HOME_MATERIAL` names, and only files."""
        source_home = self._parent_env.get("HOME")
        if not source_home:
            return
        for relative in REVIEWED_HOME_MATERIAL:
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise LaunchPolicyError(
                    "reviewed home material must be a relative path inside the home directory",
                    evidence={"path": relative},
                )
            origin = Path(source_home) / candidate
            if not origin.is_file():
                continue
            target = home / candidate
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, target)
            target.chmod(0o600)
            self._event(f"synthetic home: copied reviewed material {relative}")

    def _script_argv(
        self, argv: Sequence[str], *, lane: str, cwd: Path
    ) -> tuple[tuple[str, ...], TrustedProgram]:
        """Validate a script lane's argv and resolve its program to a trusted path.

        The child's ``PATH`` no longer contains the operator's directories, so a
        bare program name has to be resolved *here*, while the launcher still
        knows where the operator meant to look. What the child is handed is the
        absolute path that lookup produced, fingerprinted, so nothing between
        this line and the spawn can change which file runs.
        """
        checked = assert_launchable(argv)
        program = resolve_program(
            checked[0],
            search_path=resolution_path(self._parent_env.get("PATH")),
            what=lane,
            base=cwd,
            forbidden_roots=self._runtime_roots(),
        )
        return (program.path, *checked[1:]), program

    def _runtime_roots(self) -> tuple[Path, ...]:
        """Where a configured program may never resolve to.

        The launcher's whole scratch root, not just the runtime directories
        inside it: a lane's own scratch, home, and input all live there too, and
        a program resolved out of any of them is a program a lane wrote.
        """
        if self._scratch is None:
            return ()
        return (self._scratch,)

    def _assert_isolated(self, cwd: Path, *, lane: str) -> None:
        path = Path(cwd).resolve()
        if not path.is_dir():
            raise LaunchPolicyError(
                "a lane can only be launched in an existing worktree",
                evidence={"lane": lane, "cwd": str(path)},
            )
        if self._worktree_root is None:
            return
        try:
            path.relative_to(self._worktree_root)
        except ValueError as exc:
            raise LaunchPolicyError(
                "refusing to launch a lane outside this run's isolated worktree root",
                evidence={"lane": lane, "cwd": str(path), "worktree_root": str(self._worktree_root)},
            ) from exc

    # -- launching ---------------------------------------------------------
    def _launch_agent(
        self,
        agent: AgentSpec,
        *,
        prompt: str,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float | None,
        lane: str,
        material: LaneMaterial,
        channel: CapabilityChannel | None,
        writable_worktree: bool,
    ) -> CommandResult:
        budget = DEFAULT_BUDGET if timeout is None else float(timeout)
        if not BUDGET_MIN <= budget <= BUDGET_MAX:
            raise LaunchPolicyError(
                "an agent lane's budget must be between 20 and 30 minutes",
                evidence={
                    "lane": lane,
                    "budget_seconds": budget,
                    "minimum": BUDGET_MIN,
                    "maximum": BUDGET_MAX,
                },
            )
        outside = [tool for tool in agent.tools if tool not in SANDBOXED_TOOLS]
        if outside:
            raise LaunchPolicyError(
                "an agent lane may only be given tools that run inside the Bash "
                "sandbox; the model client's own file and network tools are not "
                "subject to it",
                evidence={"lane": lane, "tools": outside, "sandboxed": list(SANDBOXED_TOOLS)},
            )
        socket = str(channel.path) if channel is not None else None
        checks = {
            "worktree": str(Path(cwd)),
            "socket": socket,
            "operator_home": self._parent_env.get("HOME"),
            "writable_worktree": writable_worktree,
            "lane_writable": material.writable_roots,
            "lane_readonly": material.readonly_roots,
            "denied_roots": self._denied_roots(),
            "foreign_paths": self._foreign_paths(material),
        }
        settings = self._sandbox_settings(
            lane=lane,
            cwd=cwd,
            material=material,
            socket=socket,
            writable_worktree=writable_worktree,
        )
        program = resolve_program(
            agent.program,
            search_path=resolution_path(self._parent_env.get("PATH")),
            what=lane,
            base=cwd,
            forbidden_roots=self._runtime_roots(),
        )
        argv = assert_launchable(
            self._agent_argv(agent, prompt, program=program, settings=settings),
            settings=settings,
            setting_sources=True,
        )
        self._event(
            f"{lane}: launched with an empty MCP config, a strict launcher-owned "
            f"sandbox, tools {list(agent.tools)}, budget {int(budget)}s"
        )
        return self._launch(
            argv,
            cwd=cwd,
            env=env,
            timeout=budget,
            material=material,
            programs=(program,),
            settings=settings,
            settings_checks=checks,
        )

    def _sandbox_settings(
        self,
        *,
        lane: str,
        cwd: Path,
        material: LaneMaterial,
        socket: str | None,
        writable_worktree: bool,
    ) -> Path:
        """Generate and prove this one launch's settings file."""
        document = sandbox_document(
            worktree=Path(cwd),
            lane_scratch=material.scratch,
            home=material.home_directory,
            runtime=material.runtime.directory,
            lane_input=material.inputs,
            readable_files=(material.settings, self._empty_mcp_config()),
            socket=socket,
            writable_worktree=writable_worktree,
            operator_home=self._parent_env.get("HOME"),
            denied_roots=self._denied_roots(),
        )
        return write_sandbox_settings(material.settings, document)

    def _denied_roots(self) -> tuple[Path, ...]:
        """The roots a lane may not reach at all, denied whole and by exact path.

        The launcher's scratch directory holds every lane's material, the empty
        MCP config, and the capability broker's own files; the configured scratch
        root above it holds this run's and any other's. Both are denied, and the
        lane's own directories are allowed back inside by the longest-match rule
        in :func:`~.sandbox.decides`.
        """
        roots = [self._scratch_dir()]
        if self._scratch_root is not None:
            roots.append(self._scratch_root)
        return tuple(roots)

    def _foreign_paths(self, material: LaneMaterial) -> tuple[Path, ...]:
        """Concrete paths inside the launcher's scratch that are not this lane's.

        Named so the proof is about real neighbours rather than about prefixes:
        whatever the launcher itself has put in its scratch root — the
        launcher-side broker homes, and the capability broker's ``gh`` request
        payloads while one is in flight — plus, once a second lane has run, every
        other lane's home, scratch, runtime, and settings file.
        """
        root = self._scratch_dir()
        lanes = root / "lanes"
        # The empty MCP config is the one thing in this root every lane is
        # entitled to read — it is on the lane's argv — so it is not foreign. It
        # is still never writable; that is proved through ``lane_readonly``.
        mine = {lanes, self._empty_mcp_config()}
        foreign: list[Path] = [entry for entry in sorted(root.iterdir()) if entry not in mine]
        if lanes.is_dir():
            for sibling in sorted(lanes.iterdir()):
                if sibling == material.directory:
                    continue
                foreign.extend(
                    (
                        sibling,
                        sibling / "home",
                        sibling / "scratch",
                        sibling / "runtime",
                        sibling / "settings.json",
                    )
                )
        return tuple(foreign)

    def _agent_argv(
        self,
        agent: AgentSpec,
        prompt: str,
        *,
        program: TrustedProgram,
        settings: Path,
    ) -> tuple[str, ...]:
        """Compose the child's argv array.

        Ordering matters: ``--tools`` and ``--allowedTools`` are variadic, so
        each is terminated by the next option, and the non-variadic ``--model``
        separates the last of them from the positional prompt. Anything else
        would let the prompt be swallowed as a tool name.
        """
        if agent.permission_mode not in PERMISSION_MODES:
            raise LaunchPolicyError(
                "this permission mode is not one a child may run under",
                evidence={"permission_mode": agent.permission_mode, "allowed": list(PERMISSION_MODES)},
            )
        if not prompt or prompt.startswith("-"):
            raise LaunchPolicyError(
                "the composed prompt would be read as an option rather than a prompt",
                evidence={"prompt_prefix": prompt[:40]},
            )
        tools = ",".join(agent.tools)
        return (
            program.path,
            "--print",
            "--output-format",
            "text",
            "--settings",
            str(settings),
            SETTING_SOURCES_ENTRY,
            "--permission-mode",
            agent.permission_mode,
            "--strict-mcp-config",
            "--mcp-config",
            str(self._empty_mcp_config()),
            "--tools",
            tools,
            "--allowedTools",
            tools,
            "--model",
            agent.model,
            prompt,
        )

    def _launch(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float | None,
        material: LaneMaterial,
        programs: Sequence[TrustedProgram] = (),
        settings: Path | None = None,
        settings_checks: Mapping[str, object] | None = None,
    ) -> CommandResult:
        # The last thing before the spawn, and the point of doing it here: every
        # check above happened at some earlier moment, and this lane's runtime,
        # its program, and its settings file all had to stay what they were in
        # between.
        material.runtime.assert_intact()
        for program in programs:
            program.assert_unchanged(what=str(cwd))
        if settings is not None:
            assert_sandbox_file(settings, **dict(settings_checks or {}))
        result = self._runner.run(argv, cwd=cwd, env=env, timeout=timeout)
        return CommandResult(
            argv=result.argv,
            returncode=result.returncode,
            stdout=quiet(result.stdout),
            stderr=quiet(result.stderr),
            timed_out=result.timed_out,
        )

    # -- scratch -----------------------------------------------------------
    def _scratch_dir(self) -> Path:
        if self._scratch is None:
            root = self._scratch_root
            if root is not None:
                root.mkdir(parents=True, exist_ok=True)
            self._scratch = Path(
                tempfile.mkdtemp(prefix="pr-prover-launch-", dir=str(root) if root else None)
            )
            self._scratch.chmod(0o700)
        return self._scratch

    def _empty_mcp_config(self) -> Path:
        path = self._scratch_dir() / "mcp-empty.json"
        if not path.exists():
            path.write_text(json.dumps(_EMPTY_MCP, indent=2) + "\n", encoding="utf-8")
            path.chmod(0o600)
        return path

    def close(self) -> None:
        """Close every channel, then remove the launcher's scratch directory.

        Order matters, and it is the reason nothing is removed early.
        :meth:`~.capabilities.CapabilityChannel.close` does not return until it
        has stopped accepting, drained the handlers it accepted, cancelled and
        joined whatever was still running, and closed the listening socket — so
        by the time this method reaches the scratch tree, no brokered ``git`` or
        ``gh`` is still running out of it and nothing is listening on anything
        inside it. A channel that could *not* account for a handler records a
        refusal in :attr:`shutdown_errors`; the loop turns that into a
        fail-closed stop rather than reporting a run it cannot vouch for.

        Never raises: this runs on the way out of a run, including a failing
        one, and losing the original failure to a teardown error would be worse
        than reporting both.
        """
        for channel in list(self._open_channels):
            try:
                channel.close()
            except Exception as exc:  # pragma: no cover - defensive
                self.shutdown_errors.append(
                    LaunchPolicyError(
                        "a capability channel could not be closed",
                        evidence={"error": f"{type(exc).__name__}: {exc}"},
                    )
                )
            failure = getattr(channel, "shutdown_error", None)
            if failure is not None:
                self.shutdown_errors.append(
                    LaunchPolicyError(failure.message, evidence=failure.evidence)
                )
        self._open_channels.clear()
        for runtime in self._runtimes:
            runtime.release()
        self._runtimes.clear()
        if self._scratch is None:
            return
        shutil.rmtree(self._scratch, ignore_errors=True)
        self._scratch = None

    def observe(self, on_event: Callable[[str], None]) -> None:
        """Send launch events to a caller's log. Carries names, never credentials."""
        self._on_event = on_event

    def _event(self, message: str) -> None:
        if self._on_event is not None:
            self._on_event(message)


class _TrackedChannel(CapabilityChannel):
    """A channel that tells its broker when it closes, so ``close()`` is exact."""

    def __init__(
        self,
        broker: CapabilityBroker,
        *,
        label: str,
        broker_owner: LaunchBroker,
        on_event: Callable[[str], None] | None = None,
    ) -> None:
        self._owner = broker_owner
        super().__init__(broker, label=label, on_event=on_event)

    def close(self) -> None:
        super().close()
        self._owner._forget_channel(self)


def _required(argv: Sequence[str] | None, *, lane: str) -> Sequence[str]:
    if argv is None:
        raise LaunchPolicyError(
            "this lane has neither an argv array nor an agent launch spec",
            evidence={"lane": lane},
        )
    return argv


def _gitconfig(identity: ResolvedIdentity | None) -> str:
    """The child's whole git configuration.

    Credential helpers are cleared and none is ever put back. A child holds no
    GitHub credential, so there is nothing for a helper to offer: a direct
    ``git push`` from a lane fails for want of a credential, and the only push
    that can succeed is the one the launcher performs over the capability
    channel, against the bound branch of the bound repository.
    """
    lines = [
        "# Written by pr-prover for one child launch. The child inherits no other",
        "# git configuration: GIT_CONFIG_SYSTEM is /dev/null, HOME is a synthetic",
        "# directory this launcher made, and GIT_CONFIG_GLOBAL points here.",
        "[credential]",
        "\thelper =",
        '[credential "https://github.com"]',
        "\thelper =",
    ]
    if identity is not None:
        lines += [
            "[user]",
            f"\tname = {identity.login}",
            f"\temail = {identity.login}@users.noreply.github.com",
        ]
    lines += ["[core]", "\tpager = cat", "[advice]", "\tdetachedHead = false", ""]
    return "\n".join(lines)


def _slug(name: str) -> str:
    return _SLUG.sub("-", name.lower()) or "lane"


def file_is_owner_only(path: Path) -> bool:
    """True when only the owner can read ``path``. Used by the launcher's own tests."""
    return not Path(path).stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO)


__all__ = [
    "BUDGET_MAX",
    "BUDGET_MIN",
    "BUILDER_TOOLS",
    "DEFAULT_BUDGET",
    "FORBIDDEN_FLAGS",
    "PERMISSION_MODES",
    "REVIEWED_HOME_MATERIAL",
    "REVIEWER_TOOLS",
    "SETTING_SOURCES_ENTRY",
    "SHIM_NAME",
    "AgentSpec",
    "BoundContext",
    "LaneMaterial",
    "LaunchBroker",
    "assert_launchable",
    "file_is_owner_only",
    "quiet",
]
