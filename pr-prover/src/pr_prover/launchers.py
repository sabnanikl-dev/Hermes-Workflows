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

**A synthetic HOME.** No child inherits the operator's home directory. The
launcher builds one per lane under its own scratch and points every
configuration-discovery variable it knows about — ``GH_CONFIG_DIR``,
``GIT_CONFIG_GLOBAL``/``GIT_CONFIG_SYSTEM``, ``CLAUDE_CONFIG_DIR``,
``GNUPGHOME``, and the four XDG directories — inside it. Only material named in
:data:`REVIEWED_HOME_MATERIAL` is copied in, and that list is empty: adding to it
is a code change, not a configuration one.

**Empty MCP.** Every agent lane is launched with ``--strict-mcp-config`` and an
``--mcp-config`` file this module wrote containing no servers, so a project or
user MCP configuration cannot attach tools to a child.

**Bounded tools.** The tool set is a code-owned maximum per role, and a
configuration may only narrow it. The reviewer maximum contains no file-writing
tool at all.

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
"""
from __future__ import annotations

import json
import os
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
    write_shim,
)
from .childenv import CAPABILITY_CHANNEL, HOME_GUARDS, EnvironmentPolicy
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

# The 20-30 minute background budget, in seconds, and the default inside it.
BUDGET_MIN = 1200.0
BUDGET_MAX = 1800.0
DEFAULT_BUDGET = 1500.0

# Code-owned tool maxima. A configuration may narrow these; it can never widen
# them. The reviewer set has no Edit, no Write, and no NotebookEdit: a reviewer
# that cannot write a file cannot "fix" one on its way past a finding.
BUILDER_TOOLS = ("Bash", "Edit", "Glob", "Grep", "Read", "TodoWrite", "Write")
REVIEWER_TOOLS = ("Bash", "Glob", "Grep", "Read", "TodoWrite")

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


def assert_launchable(argv: Sequence[str]) -> tuple[str, ...]:
    """Reject an argv array that would broaden a child's authority."""
    checked = validate_argv(argv, what="child launch")
    for index, item in enumerate(checked):
        flag = item.split("=", 1)[0]
        if flag in FORBIDDEN_FLAGS:
            raise LaunchPolicyError(
                "this launch would give the child authority the launcher does not own",
                evidence={"flag": flag, "index": index, "forbidden": list(FORBIDDEN_FLAGS)},
            )
    return checked


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
        self._shim: Path | None = None
        self._resolved: dict[str, ResolvedIdentity] = {}
        self._verified: set[str] = set()
        self._open_channels: list[CapabilityChannel] = []
        self.channels: list[CapabilityChannel] = []

    # -- lanes -------------------------------------------------------------
    def run_gate(
        self, *, name: str, argv: Sequence[str], cwd: Path, timeout: float | None
    ) -> CommandResult:
        """Run a repository gate with no GitHub identity and no capability channel."""
        lane = f"gate {name}"
        self._assert_isolated(cwd, lane=lane)
        env = self._environment(identity=None, cwd=cwd, bound=None, lane=lane, channel=None)
        return self._launch(assert_launchable(argv), cwd=cwd, env=env, timeout=timeout)

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
            env = self._environment(
                identity=resolved,
                cwd=cwd,
                bound=bound,
                lane=lane,
                channel=channel,
                extra={"PR_PROVER_ROLE": role},
            )
            if agent is None:
                return self._launch(
                    assert_launchable(_required(argv, lane=lane)),
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
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
                agent, prompt=prompt, cwd=cwd, env=env, timeout=timeout, lane=lane
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
            env = self._environment(
                identity=resolved,
                cwd=cwd,
                bound=bound,
                lane=lane,
                channel=channel,
                extra={
                    "PR_PROVER_ATTEMPT": str(attempt),
                    "PR_PROVER_MODE": mode,
                    "PR_PROVER_BLOCKERS_FILE": str(blockers_file),
                },
            )
            if agent is None:
                return self._launch(
                    assert_launchable(_required(argv, lane=lane)),
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
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
                blockers_file=str(blockers_file),
                signature=signature,
            )
            return self._launch_agent(
                agent, prompt=prompt, cwd=cwd, env=env, timeout=timeout, lane=lane
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
        home = self._home_for(f"broker-{_slug(identity.spec.name)}", identity=identity)
        return identity.broker_env(
            {
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
        channel = _TrackedChannel(broker, label=_slug(lane), broker_owner=self)
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
    def _environment(
        self,
        *,
        identity: ResolvedIdentity | None,
        cwd: Path,
        bound: BoundContext | None,
        lane: str,
        channel: CapabilityChannel | None,
        extra: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        inject = self._home_for(_slug(lane), identity=identity)
        inject["PATH"] = self._child_path()
        if channel is not None:
            inject[CAPABILITY_CHANNEL] = str(channel.path)
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
        }
        if bound is not None:
            overrides.update(bound.env())
        overrides.update(extra or {})
        overrides["PR_PROVER_LANE"] = lane
        return self._policy.build(self._parent_env, inject=inject, overrides=overrides)

    def _home_for(self, slug: str, *, identity: ResolvedIdentity | None) -> dict[str, str]:
        """Build one synthetic home and return the variables that point inside it.

        A child never sees the operator's home directory. ``gh``, ``git``,
        ``gpg``, the model client, and everything that follows the XDG
        convention are all pointed at directories this launcher made, so a
        toolchain that goes looking for stored credentials finds an empty tree
        rather than the operator's.
        """
        home = self._scratch_dir() / "home" / slug
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

    def _child_path(self) -> str:
        """The child's ``PATH``: the capability shim first, then the operator's."""
        inherited = self._parent_env.get("PATH") or _FALLBACK_PATH
        return os.pathsep.join([str(self._shim_dir()), inherited])

    def _shim_dir(self) -> Path:
        if self._shim is None:
            self._shim = write_shim(self._scratch_dir() / "bin").parent
        return self._shim

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
        argv = assert_launchable(self._agent_argv(agent, prompt))
        self._event(
            f"{lane}: launched with an empty MCP config, tools {list(agent.tools)}, "
            f"budget {int(budget)}s"
        )
        return self._launch(argv, cwd=cwd, env=env, timeout=budget)

    def _agent_argv(self, agent: AgentSpec, prompt: str) -> tuple[str, ...]:
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
            agent.program,
            "--print",
            "--output-format",
            "text",
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
    ) -> CommandResult:
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

        Order matters. :class:`~.commands.SubprocessRunner` does not return
        until a lane's whole process group is gone, so by the time this runs no
        descendant is still holding a socket or a synthetic home — but the
        channels are closed first regardless, so the scratch tree is removed
        only after nothing is listening on anything inside it.
        """
        for channel in list(self._open_channels):
            channel.close()
        self._open_channels.clear()
        if self._scratch is None:
            return
        shutil.rmtree(self._scratch, ignore_errors=True)
        self._scratch = None
        self._shim = None

    def observe(self, on_event: Callable[[str], None]) -> None:
        """Send launch events to a caller's log. Carries names, never credentials."""
        self._on_event = on_event

    def _event(self, message: str) -> None:
        if self._on_event is not None:
            self._on_event(message)


class _TrackedChannel(CapabilityChannel):
    """A channel that tells its broker when it closes, so ``close()`` is exact."""

    def __init__(self, broker: CapabilityBroker, *, label: str, broker_owner: LaunchBroker) -> None:
        self._owner = broker_owner
        super().__init__(broker, label=label)

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
    "SHIM_NAME",
    "AgentSpec",
    "BoundContext",
    "LaunchBroker",
    "assert_launchable",
    "file_is_owner_only",
    "quiet",
]
