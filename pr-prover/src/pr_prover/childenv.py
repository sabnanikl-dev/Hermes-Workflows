"""The explicit child environment allowlist.

Every child the loop launches gets an environment built here from nothing. The
parent's environment is never inherited wholesale, because inheritance is how a
merge-capable token, a deploy key, or an agent socket reaches a child nobody
meant to trust with it.

Three rules, in this order:

**Deny wins.** A name that looks like a credential is dropped even if something
else allowed it. The check is on the *name*, so an unfamiliar
``ACME_DEPLOY_TOKEN`` is refused without anyone having to enumerate it first.

**Allow is explicit.** Only names on the allowlist survive, so the default for
anything new is "not passed".

**Injection is owned.** The launcher declares, up front, the exact names it
injects; nothing else may write a denied name. That is what makes "the launcher
is the only credential broker" checkable rather than aspirational.

Two inherited names deserve their own note. ``HOME`` is allowed, because the
model client and the toolchain need it — but on its own it is a hole: ``gh``
falls back to ``~/.config/gh/hosts.yml`` and ``git`` to ``~/.gitconfig`` and the
OS keychain, either of which can carry far more authority than the identity the
launcher meant to hand over. So a launcher that allows ``HOME`` must also
redirect ``GH_CONFIG_DIR`` and ``GIT_CONFIG_GLOBAL`` at files it wrote itself;
:func:`assert_scoped` refuses an environment that allows ``HOME`` without them.

``SSH_AUTH_SOCK`` is denied outright: a forwarded agent is push authority for
every repository the key can reach, which is exactly the blast radius this
module exists to remove.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .errors import LaunchPolicyError

# Names a child may inherit. Deliberately short: locale, paths, and the
# toolchain basics, with nothing that carries authority.
DEFAULT_ALLOW = frozenset(
    {
        "HOME",
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

# The redirections that make an allowed HOME safe. A launcher sets both to
# files it wrote; inheriting either is denied.
_HOME_GUARDS = ("GH_CONFIG_DIR", "GIT_CONFIG_GLOBAL")

# Names a launcher may set that carry no authority: quiet/progress discipline
# and the refusal to prompt for credentials. Listed here so that "the launcher
# owns this variable" stays a closed set rather than anything a launcher writes.
LAUNCHER_OVERRIDES = frozenset(
    {
        "CI",
        "CLICOLOR",
        "COLUMNS",
        "GIT_TERMINAL_PROMPT",
        "NO_COLOR",
        "PAGER",
        "TERM",
    }
)

# Denied by exact name: GitHub authority, credential-helper hooks, and the
# agent sockets that are authority in their own right.
_DENY_EXACT = frozenset(
    {
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
        "SSH_AGENT_PID",
        "SSH_ASKPASS",
        "SSH_AUTH_SOCK",
        "SUDO_ASKPASS",
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

# Names no configuration may pass through or hand to a launcher as an
# injection, whatever else it claims. This is the floor: GitHub authority and
# the shell hooks that turn into it.
NEVER_PERMITTED = frozenset(
    {
        "GH_ENTERPRISE_TOKEN",
        "GH_HOST",
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


@dataclass(frozen=True)
class EnvironmentPolicy:
    """Which parent variables a child may inherit, and which it may never.

    ``extra_allow`` is the only configurable widening, and it cannot reach a
    denied name: a configuration that lists ``DEPLOY_TOKEN`` there is refused
    when the policy is built, not quietly honoured.

    ``permit`` is narrower still and exists for one case: model access for an
    agent lane, where the child needs an API key that is not repository, deploy,
    or client authority. Every name in it is checked against
    :data:`NEVER_PERMITTED`, so it can never become a way to hand back GitHub.
    """

    extra_allow: frozenset[str] = frozenset()
    permit: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        for name in sorted(self.extra_allow):
            validate_env_name(name, what="launch.env_allow entry")
            if is_denied(name):
                raise LaunchPolicyError(
                    "launch.env_allow names a credential-shaped variable; the child "
                    "environment allowlist cannot be widened to include one",
                    evidence={"name": name},
                )
        for name in sorted(self.permit):
            validate_env_name(name, what="launch.model_auth_env")
            if name.upper() in NEVER_PERMITTED:
                raise LaunchPolicyError(
                    "this variable can never be passed to a child",
                    evidence={"name": name, "never_permitted": sorted(NEVER_PERMITTED)},
                )

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

        ``inject`` is the launcher's owned material — the one scoped credential
        and the redirections that keep the toolchain from finding another one.
        ``overrides`` is launcher-owned too, but carries no authority: quiet
        output settings and the bound repo/PR/head context.
        """
        child: dict[str, str] = {}
        for name in sorted(self.allow):
            if is_denied(name) and name not in self.permit:
                continue
            value = parent.get(name)
            if isinstance(value, str):
                child[name] = value
        for name, value in (overrides or {}).items():
            validate_env_name(name, what="launcher override")
            if name not in LAUNCHER_OVERRIDES and not name.startswith("PR_PROVER_"):
                raise LaunchPolicyError(
                    "a launcher may only override quiet-output settings and PR_PROVER_ "
                    "context; anything else must be a declared injection",
                    evidence={"name": name, "overrides": sorted(LAUNCHER_OVERRIDES)},
                )
            child[name] = _text(name, value)
        for name, value in (inject or {}).items():
            validate_env_name(name, what="injected variable")
            child[name] = _text(name, value)
        assert_scoped(child, injected=frozenset(inject or {}), policy=self)
        return child

    def dropped(self, parent: Mapping[str, str]) -> tuple[str, ...]:
        """The parent names this policy refuses to pass on. Names only, never values."""
        return tuple(sorted(name for name in parent if name not in self.allow or is_denied(name)))


def assert_scoped(
    env: Mapping[str, str], *, injected: frozenset[str], policy: EnvironmentPolicy
) -> None:
    """Prove a composed environment carries nothing beyond its declared scope.

    The last check before a child is launched, and the one an added feature has
    to get past: every name is either allowlisted or a declared injection, and
    no denied name survives unless the launcher owns it.
    """
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
    if "HOME" in env and not all(guard in injected for guard in _HOME_GUARDS):
        raise LaunchPolicyError(
            "a child that inherits HOME must be given launcher-owned GH_CONFIG_DIR and "
            "GIT_CONFIG_GLOBAL, or gh and git fall back to the parent's stored credentials",
            evidence={"missing": sorted(set(_HOME_GUARDS) - injected)},
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
    "DEFAULT_ALLOW",
    "LAUNCHER_OVERRIDES",
    "NEVER_PERMITTED",
    "EnvironmentPolicy",
    "assert_scoped",
    "carries_none_of",
    "is_denied",
    "validate_env_name",
]
