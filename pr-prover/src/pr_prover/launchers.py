"""The hardened launchers: the only place a child gets an environment.

Every lane the loop runs — a baseline gate, a reviewer, the builder — is
launched through :class:`LaunchBroker`. The broker builds the child's
environment from nothing (:mod:`.childenv`), hands over at most the one scoped
identity that lane owns (:mod:`.identities`), and, for an agent lane, builds the
whole argv array itself from a code-owned prompt (:mod:`.prompts`).

Launch discipline lives here as code rather than as instructions somebody
remembers to follow:

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

Two refusals are worth naming. A caller may not pass an environment into
:meth:`LaunchBroker.run_gate` and friends: an environment assembled anywhere
else is exactly the runtime override that would put the authority back. And a
composed agent argv is re-scanned for authority-broadening flags before launch,
so a future edit that threads ``--dangerously-skip-permissions`` or
``--add-dir`` in from configuration fails closed instead of shipping.

Nothing here trusts a child's own account of what it did. The broker proves
which account a credential is *before* the launch; the loop proves what landed
on GitHub *after* it.
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

from .childenv import EnvironmentPolicy
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
        self._resolved: dict[str, ResolvedIdentity] = {}
        self._verified: set[str] = set()

    # -- lanes -------------------------------------------------------------
    def run_gate(
        self, *, name: str, argv: Sequence[str], cwd: Path, timeout: float | None
    ) -> CommandResult:
        """Run a repository gate with no GitHub identity at all."""
        env = self._environment(identity=None, cwd=cwd, bound=None, lane=f"gate {name}")
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
        resolved = self._identity_for(lane, identity, required=REVIEWER_CAPABILITIES)
        env = self._environment(
            identity=resolved, cwd=cwd, bound=bound, lane=lane, extra={"PR_PROVER_ROLE": role}
        )
        if agent is None:
            return self._launch(
                assert_launchable(_required(argv, lane=lane)), cwd=cwd, env=env, timeout=timeout
            )
        prompt = reviewer_prompt(
            repo=bound.repo,
            pr=bound.pr,
            branch=bound.branch,
            head=bound.head,
            worktree=str(cwd),
            login=_identified(resolved, lane=lane).login,
            role=role,
        )
        return self._launch_agent(agent, prompt=prompt, cwd=cwd, env=env, timeout=timeout, lane=lane)

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
        resolved = self._identity_for(lane, identity, required=BUILDER_CAPABILITIES)
        env = self._environment(
            identity=resolved,
            cwd=cwd,
            bound=bound,
            lane=lane,
            extra={
                "PR_PROVER_ATTEMPT": str(attempt),
                "PR_PROVER_MODE": mode,
                "PR_PROVER_BLOCKERS_FILE": str(blockers_file),
            },
        )
        if agent is None:
            return self._launch(
                assert_launchable(_required(argv, lane=lane)), cwd=cwd, env=env, timeout=timeout
            )
        prompt = builder_prompt(
            repo=bound.repo,
            pr=bound.pr,
            branch=bound.branch,
            head=bound.head,
            worktree=str(cwd),
            login=_identified(resolved, lane=lane).login,
            attempt=attempt,
            mode=mode,
            blockers_file=str(blockers_file),
            signature=signature,
        )
        return self._launch_agent(agent, prompt=prompt, cwd=cwd, env=env, timeout=timeout, lane=lane)

    # -- identities --------------------------------------------------------
    def _identity_for(
        self, lane: str, name: str | None, *, required: frozenset[str]
    ) -> ResolvedIdentity | None:
        if name is None:
            return None
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

    def _verify(self, identity: ResolvedIdentity, env: Mapping[str, str], *, lane: str, repo: str) -> None:
        """Prove the credential is this account, with no authority beyond its capabilities."""
        if identity.spec.name in self._verified:
            return
        if self._verifier is None:
            raise LaunchPolicyError(
                "a lane declares a scoped identity but no verifier is available to "
                "prove which account it is; refusing to launch on an unverified credential",
                evidence={"lane": lane, "identity": identity.spec.name},
            )
        facts = self._verifier.facts(env, repo=repo)
        assert_scope(identity, facts, repo=repo, lane=lane)
        self._verified.add(identity.spec.name)
        self._event(
            f"{lane}: credential verified as {facts.login} with "
            f"{sorted(name for name, held in facts.permissions.items() if held)} on {repo}"
        )

    # -- environment -------------------------------------------------------
    def _environment(
        self,
        *,
        identity: ResolvedIdentity | None,
        cwd: Path,
        bound: BoundContext | None,
        lane: str,
        extra: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        self._assert_isolated(cwd, lane=lane)
        slug = _slug(identity.spec.name if identity else "anonymous")
        inject = self._toolchain_guards(slug, identity)
        overrides: dict[str, str] = {
            "CI": "1",
            "NO_COLOR": "1",
            "CLICOLOR": "0",
            "TERM": "dumb",
            "PAGER": "cat",
            "COLUMNS": "200",
            "GIT_TERMINAL_PROMPT": "0",
        }
        if bound is not None:
            overrides.update(bound.env())
        overrides.update(extra or {})
        overrides["PR_PROVER_LANE"] = lane
        if identity is not None:
            inject.update(identity.injection())
        env = self._policy.build(self._parent_env, inject=inject, overrides=overrides)
        if identity is not None and bound is not None:
            self._verify(identity, env, lane=lane, repo=bound.repo)
        return env

    def _toolchain_guards(self, slug: str, identity: ResolvedIdentity | None) -> dict[str, str]:
        """Point ``gh`` and ``git`` at launcher-owned configuration.

        Without this, a child that inherits ``HOME`` reaches the operator's
        ``gh`` login and the OS keychain, and the scoped credential becomes
        decoration.
        """
        home = self._scratch_dir() / slug
        gh_config = home / "gh"
        gh_config.mkdir(parents=True, exist_ok=True)
        gh_config.chmod(0o700)
        gitconfig = home / "gitconfig"
        gitconfig.write_text(_gitconfig(identity), encoding="utf-8")
        gitconfig.chmod(0o600)
        return {
            "GH_CONFIG_DIR": str(gh_config),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_SYSTEM": "/dev/null",
        }

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
        self._event(f"{lane}: launched with an empty MCP config, tools {list(agent.tools)}, budget {int(budget)}s")
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
        """Remove the launcher's scratch directory, credentials on disk included."""
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


def _identified(identity: ResolvedIdentity | None, *, lane: str) -> ResolvedIdentity:
    """An agent lane without a scoped identity has nothing to act as. Fail closed."""
    if identity is None:
        raise LaunchPolicyError(
            "an agent lane must be bound to one scoped identity",
            evidence={"lane": lane},
        )
    return identity


def _required(argv: Sequence[str] | None, *, lane: str) -> Sequence[str]:
    if argv is None:
        raise LaunchPolicyError(
            "this lane has neither an argv array nor an agent launch spec",
            evidence={"lane": lane},
        )
    return argv


def _gitconfig(identity: ResolvedIdentity | None) -> str:
    """The child's whole git configuration.

    Credential helpers are cleared first, so the OS keychain and any inherited
    helper are unreachable. A lane that may push gets exactly one helper back:
    ``gh``, which can only offer the scoped token this launcher injected. A lane
    with no push capability gets no helper at all, so an attempted push fails
    for want of a credential rather than on trust.
    """
    lines = [
        "# Written by pr-prover for one child launch. The child inherits no other",
        "# git configuration: GIT_CONFIG_SYSTEM is /dev/null and HOME's config is",
        "# overridden by GIT_CONFIG_GLOBAL.",
        "[credential]",
        "\thelper =",
        '[credential "https://github.com"]',
        "\thelper =",
    ]
    if identity is not None and "push-branch" in identity.spec.capabilities:
        lines.append("\thelper = !gh auth git-credential")
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
    "REVIEWER_TOOLS",
    "AgentSpec",
    "BoundContext",
    "LaunchBroker",
    "assert_launchable",
    "file_is_owner_only",
    "quiet",
]
