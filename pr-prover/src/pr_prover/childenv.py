"""The explicit child environment allowlist.

Every child the loop launches gets an environment built here from nothing. The
parent's environment is never inherited wholesale, because inheritance is how a
merge-capable token, a deploy key, or an agent socket reaches a child nobody
meant to trust with it.

Four rules, in this order:

**Deny wins.** A name that looks like a credential is dropped even if something
else allowed it. The check is on the *name*, so an unfamiliar
``ACME_DEPLOY_TOKEN`` is refused without anyone having to enumerate it first.

**Allow is explicit.** Only names on the allowlist survive, so the default for
anything new is "not passed".

**Injection is a closed set.** A launcher does not get to name what it injects.
:data:`INJECTABLE` is the whole list — a synthetic ``HOME``, the ``PATH`` that
reaches the capability shim, the redirections that keep the toolchain from
discovering the operator's configuration, and exactly one internal broker
channel. A credential cannot be injected under an arbitrary name because there
is no arbitrary name to inject it under, and no child is given a GitHub
credential at all (see :mod:`.capabilities`).

**Model access is a channel, not a variable name.** A configuration cannot name
the environment variable that carries model credentials; it picks one of the
code-owned channels in :data:`MODEL_AUTH_CHANNELS`, and the variable name comes
from this module. ``GH_TOKEN``, ``JMD_DEPLOY_KEY``, ``VERCEL_TOKEN``,
``AWS_SECRET_ACCESS_KEY`` and ``KARAN_APPROVAL_TOKEN`` are therefore not
expressible there, rather than merely rejected there.

``HOME`` is the one name that used to be inherited and is now synthesised. A
child that inherits the operator's home directory reaches ``~/.config/gh``,
``~/.gitconfig``, ``~/.ssh``, the OS keychain, and the model client's own stored
credentials, so the launcher builds a home of its own instead and points every
configuration-discovery variable it knows about inside it.

``SSH_AUTH_SOCK`` is denied outright: a forwarded agent is push authority for
every repository the key can reach, which is exactly the blast radius this
module exists to remove.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .errors import LaunchPolicyError

# Names a child may inherit. Deliberately short: locale, paths, and the
# toolchain basics, with nothing that carries authority. HOME is absent on
# purpose — the launcher synthesises one.
DEFAULT_ALLOW = frozenset(
    {
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LOGNAME",
        "PATH",
        "SHELL",
        "TMPDIR",
        "TZ",
        "USER",
    }
)

# The redirections that make a synthetic HOME actually close off discovery. A
# launcher writes all of them; inheriting any of them is denied.
HOME_GUARDS = (
    "CLAUDE_CONFIG_DIR",
    "GH_CONFIG_DIR",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
    "GNUPGHOME",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
)

# The one internal channel a child is given: the path of a launcher-owned unix
# socket that serves the narrow capability operations in :mod:`.capabilities`.
# It carries no credential; it is a rendezvous point, and the launcher on the
# other end is what actually holds authority.
CAPABILITY_CHANNEL = "PR_PROVER_CAPABILITY_SOCKET"

# Everything a launcher may inject, in full. Anything outside this set fails
# closed, so "the launcher is the only credential broker" cannot decay into
# "the launcher may write whatever it likes".
INJECTABLE = frozenset({"HOME", "PATH", CAPABILITY_CHANNEL, *HOME_GUARDS})

# Names a launcher may set that carry no authority: quiet/progress discipline,
# the refusal to prompt for credentials, and the refusal to litter a read-only
# worktree with bytecode. Listed here so that "the launcher owns this variable"
# stays a closed set rather than anything a launcher writes.
LAUNCHER_OVERRIDES = frozenset(
    {
        "CI",
        "CLICOLOR",
        "COLUMNS",
        "GIT_TERMINAL_PROMPT",
        "NO_COLOR",
        "PAGER",
        "PYTHONDONTWRITEBYTECODE",
        "TERM",
    }
)

# The model-access channels a configuration may pick from, keyed by the name a
# configuration writes. The environment variable is this module's to choose,
# which is what makes "a configuration cannot name a GitHub, deploy, client, or
# approval credential" a property of the vocabulary rather than a filter.
MODEL_AUTH_CHANNELS: Mapping[str, str] = MappingProxyType(
    {
        "anthropic-api-key": "ANTHROPIC_API_KEY",
        "claude-code-oauth-token": "CLAUDE_CODE_OAUTH_TOKEN",
    }
)

# Denied by exact name: GitHub authority, credential-helper hooks, and the
# agent sockets that are authority in their own right.
_DENY_EXACT = frozenset(
    {
        "CLAUDE_CONFIG_DIR",
        "GH_CONFIG_DIR",
        "GH_ENTERPRISE_TOKEN",
        "GH_HOST",
        "GITHUB_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "GIT_ASKPASS",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_PROXY_COMMAND",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "GNUPGHOME",
        "GPG_AGENT_INFO",
        "HOME",
        "SSH_AGENT_PID",
        "SSH_ASKPASS",
        "SSH_AUTH_SOCK",
        "SUDO_ASKPASS",
        # The XDG directories. Not credentials themselves, but inheriting one
        # points a toolchain straight back at the operator's stored settings and
        # tokens, which is the whole point of building a synthetic home.
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    }
)

# Denied by substring: the vocabulary credentials are named in.
_DENY_SUBSTRING = (
    "APIKEY",
    "API_KEY",
    "AUTH",
    "COOKIE",
    "CREDENTIAL",
    "PASSPHRASE",
    "PASSWD",
    "PASSWORD",
    "PRIVATE_KEY",
    "SECRET",
    "SESSION",
    "SIGNING_KEY",
    "TOKEN",
)

# Denied by prefix: whole vendors, so a new variable from one of them is
# refused before anybody has heard of it. Hosting, deploy, client systems,
# package registries, and secret managers.
_DENY_PREFIX = (
    "ANTHROPIC_",
    "AWS_",
    "AZURE_",
    "CF_",
    "CLOUDFLARE_",
    "DIGITALOCEAN_",
    "DOCKER_",
    "FASTLY_",
    "FLY_",
    "GCLOUD_",
    "GCP_",
    "GOOGLE_",
    "HEROKU_",
    "JMD_",
    "KARAN_",
    "KUBE_",
    "LINEAR_",
    "MAILGUN_",
    "N8N_",
    "NETLIFY_",
    "NOTION_",
    "NPM_",
    "OP_",
    "OPENAI_",
    "PYPI_",
    "RENDER_",
    "SANITY_",
    "SENDGRID_",
    "SLACK_",
    "STRIPE_",
    "TELEGRAM_",
    "TWILIO_",
    "VERCEL_",
)

# Names no configuration may pass through, and no launcher may inject, whatever
# else it claims. This is the floor: GitHub authority and the shell hooks that
# turn into it.
NEVER_PERMITTED = frozenset(
    {
        "GH_ENTERPRISE_TOKEN",
        "GH_HOST",
        "GH_TOKEN",
        "GITHUB_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
        "GIT_ASKPASS",
        "GIT_SSH_COMMAND",
        "SSH_ASKPASS",
        "SSH_AUTH_SOCK",
    }
)

_ENV_NAME = re.compile(r"\A[A-Za-z_][A-Za-z0-9_]*\Z")


def is_denied(name: str) -> bool:
    """True when ``name`` may never be inherited from the parent environment."""
    upper = name.upper()
    if upper in _DENY_EXACT:
        return True
    if any(fragment in upper for fragment in _DENY_SUBSTRING):
        return True
    return any(upper.startswith(prefix) for prefix in _DENY_PREFIX)


def validate_env_name(name: object, *, what: str) -> str:
    """Accept only a plausible environment variable name."""
    if not isinstance(name, str) or not _ENV_NAME.match(name):
        raise LaunchPolicyError(
            f"{what} is not a usable environment variable name",
            evidence={"what": what, "name": name if isinstance(name, str) else type(name).__name__},
        )
    return name


def model_auth_variable(channel: object) -> str:
    """The environment variable one code-owned model-access channel uses."""
    if not isinstance(channel, str) or channel not in MODEL_AUTH_CHANNELS:
        raise LaunchPolicyError(
            "launch.model_auth must name one of this launcher's model-access channels; "
            "an environment variable name is not accepted, so no GitHub, deploy, "
            "client, live-system, account, or approval credential can be named here",
            evidence={"model_auth": channel, "channels": sorted(MODEL_AUTH_CHANNELS)},
        )
    return MODEL_AUTH_CHANNELS[channel]


def _assert_channels_are_disjoint() -> None:
    """No model-access channel may collide with launcher-owned machinery.

    Checked once, at import, so a future channel that shadows ``PATH``, a home
    guard, the broker channel, a quiet override, or a never-permitted name is a
    build-time failure rather than a runtime surprise.
    """
    reserved = (
        DEFAULT_ALLOW
        | INJECTABLE
        | LAUNCHER_OVERRIDES
        | NEVER_PERMITTED
        | frozenset(HOME_GUARDS)
        | {"HOME", "PATH"}
    )
    for channel, name in MODEL_AUTH_CHANNELS.items():
        validate_env_name(name, what=f"model-access channel {channel!r}")
        if name in reserved or name.startswith("PR_PROVER_"):
            raise LaunchPolicyError(  # pragma: no cover - a build-time invariant
                "a model-access channel collides with a launcher-owned variable",
                evidence={"channel": channel, "name": name},
            )


_assert_channels_are_disjoint()


@dataclass(frozen=True)
class EnvironmentPolicy:
    """Which parent variables a child may inherit, and which it may never.

    ``extra_allow`` is the only configurable widening, and it cannot reach a
    denied name: a configuration that lists ``DEPLOY_TOKEN`` there is refused
    when the policy is built, not quietly honoured.

    ``model_auth`` is narrower still and exists for one case: model access for
    an agent lane. It names a *channel* from :data:`MODEL_AUTH_CHANNELS`, never
    a variable, so it cannot become a way to hand back GitHub, deploy, client,
    live-system, or approval authority.
    """

    extra_allow: frozenset[str] = frozenset()
    model_auth: str | None = None

    def __post_init__(self) -> None:
        for name in sorted(self.extra_allow):
            validate_env_name(name, what="launch.env_allow entry")
            if is_denied(name):
                raise LaunchPolicyError(
                    "launch.env_allow names a credential-shaped variable; the child "
                    "environment allowlist cannot be widened to include one",
                    evidence={"name": name},
                )
            if name in INJECTABLE or name in LAUNCHER_OVERRIDES or name.startswith("PR_PROVER_"):
                raise LaunchPolicyError(
                    "launch.env_allow names a launcher-owned variable; the launcher "
                    "writes this one and a parent value may not shadow it",
                    evidence={"name": name, "reserved": sorted(INJECTABLE | LAUNCHER_OVERRIDES)},
                )
        if self.model_auth is not None:
            model_auth_variable(self.model_auth)

    @property
    def permit(self) -> frozenset[str]:
        """The single model-access variable this policy passes through, if any."""
        if self.model_auth is None:
            return frozenset()
        return frozenset({model_auth_variable(self.model_auth)})

    @property
    def allow(self) -> frozenset[str]:
        return DEFAULT_ALLOW | self.extra_allow | self.permit

    def build(
        self,
        parent: Mapping[str, str],
        *,
        inject: Mapping[str, str] | None = None,
        overrides: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        """Build a child environment from nothing.

        ``inject`` is the launcher's owned material — the synthetic home, the
        shim-bearing ``PATH``, the redirections that keep the toolchain from
        finding the operator's configuration, and the one broker channel.
        ``overrides`` is launcher-owned too, but carries no authority: quiet
        output settings and the bound repo/PR/head context.
        """
        injected = dict(inject or {})
        child: dict[str, str] = {}
        for name in sorted(self.allow):
            if is_denied(name) and name not in self.permit:
                continue
            value = parent.get(name)
            if isinstance(value, str):
                child[name] = value
        for name, value in (overrides or {}).items():
            validate_env_name(name, what="launcher override")
            if name in injected or name in INJECTABLE:
                raise LaunchPolicyError(
                    "a launcher override collides with launcher-owned injected material; "
                    "one variable cannot have two owners",
                    evidence={"name": name, "injectable": sorted(INJECTABLE)},
                )
            if name not in LAUNCHER_OVERRIDES and not name.startswith("PR_PROVER_"):
                raise LaunchPolicyError(
                    "a launcher may only override quiet-output settings and PR_PROVER_ "
                    "context; anything else must be a declared injection",
                    evidence={"name": name, "overrides": sorted(LAUNCHER_OVERRIDES)},
                )
            child[name] = _text(name, value)
        for name, value in injected.items():
            validate_env_name(name, what="injected variable")
            child[name] = _text(name, value)
        assert_scoped(
            child,
            injected=frozenset(injected),
            policy=self,
            parent_home=parent.get("HOME"),
        )
        return child

    def dropped(self, parent: Mapping[str, str]) -> tuple[str, ...]:
        """The parent names this policy refuses to pass on. Names only, never values."""
        return tuple(sorted(name for name in parent if name not in self.allow or is_denied(name)))


def assert_scoped(
    env: Mapping[str, str],
    *,
    injected: frozenset[str],
    policy: EnvironmentPolicy,
    parent_home: str | None = None,
) -> None:
    """Prove a composed environment carries nothing beyond its declared scope.

    The last check before a child is launched, and the one an added feature has
    to get past: every name is either allowlisted, a launcher override, bound
    context, or one of the closed set of injections; no denied name survives
    unless the launcher owns it; and the home the child gets is the launcher's,
    not the operator's.
    """
    outside = sorted(injected - INJECTABLE)
    if outside:
        raise LaunchPolicyError(
            "a launcher tried to inject a variable outside the closed injectable set; "
            "credentials are brokered over the capability channel, never injected",
            evidence={"names": outside, "injectable": sorted(INJECTABLE)},
        )
    for name in sorted(env):
        if name in injected:
            if name.upper() in NEVER_PERMITTED:
                raise LaunchPolicyError(
                    "a launcher tried to inject a variable that can never be passed to a child",
                    evidence={"name": name},
                )
            continue
        if is_denied(name) and name not in policy.permit:
            raise LaunchPolicyError(
                "the composed child environment still carries a credential-shaped variable",
                evidence={"name": name, "injected": sorted(injected)},
            )
        if (
            name not in policy.allow
            and name not in LAUNCHER_OVERRIDES
            and not name.startswith("PR_PROVER_")
        ):
            raise LaunchPolicyError(
                "the composed child environment carries a variable outside the allowlist",
                evidence={"name": name, "allow": sorted(policy.allow)},
            )
    home = env.get("HOME")
    if home is None or "HOME" not in injected:
        raise LaunchPolicyError(
            "a child must be given a launcher-owned synthetic HOME; inheriting the "
            "operator's home directory hands over gh, git, ssh, and model-client "
            "configuration along with it",
            evidence={"home_present": home is not None, "home_injected": "HOME" in injected},
        )
    if parent_home is not None and home == parent_home:
        raise LaunchPolicyError(
            "the child's HOME is the operator's own home directory",
            evidence={"home": home},
        )
    missing = sorted(guard for guard in HOME_GUARDS if guard not in injected)
    if missing:
        raise LaunchPolicyError(
            "a child with a synthetic HOME must also be given every launcher-owned "
            "configuration redirection, or a toolchain falls back to the operator's",
            evidence={"missing": missing},
        )


def _text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise LaunchPolicyError(
            "child environment values must be strings",
            evidence={"name": name, "type": type(value).__name__},
        )
    return value


def carries_none_of(env: Mapping[str, str], values: Iterable[str]) -> bool:
    """True when no value in ``values`` appears anywhere in ``env``. For tests and audits."""
    haystack = "\n".join(f"{name}={value}" for name, value in env.items())
    return not any(value and value in haystack for value in values)


__all__ = [
    "CAPABILITY_CHANNEL",
    "DEFAULT_ALLOW",
    "HOME_GUARDS",
    "INJECTABLE",
    "LAUNCHER_OVERRIDES",
    "MODEL_AUTH_CHANNELS",
    "NEVER_PERMITTED",
    "EnvironmentPolicy",
    "assert_scoped",
    "carries_none_of",
    "is_denied",
    "model_auth_variable",
    "validate_env_name",
]
