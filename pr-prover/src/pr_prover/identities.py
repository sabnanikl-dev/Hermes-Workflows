"""The scoped identities a launcher may hand to a child, and nothing else.

A child never authenticates as the operator. It authenticates as one declared
identity with one declared capability set, and the launcher is the only thing
that can put that credential anywhere.

Three capabilities exist, and the set is closed::

    push-branch    push commits to the one bound PR branch
    comment-pr     post a conversation comment on the one bound PR
    review-pr      submit a review on the one bound PR

There is deliberately no ``merge-pr``, no ``approve``, no ``deploy``, and no
``admin``: a configuration naming one is rejected when it is read, so the
absence of merge authority is a property of the vocabulary rather than a rule
somebody has to remember to apply.

The credential itself never appears in the repository. A configuration names
where to read it from — a parent environment variable or a file the operator
protects — and :func:`resolve` reads it at launch time. Anything ambiguous
about that read (missing, empty, unreadable, world-readable, more than one
source) fails closed, because a launcher that cannot say exactly which identity
it is about to hand over should not hand one over.

What the identity can actually do is then checked against GitHub itself.
:class:`IdentityVerifier` reports the login the credential resolves to and the
permissions it holds on the bound repository, and :func:`assert_scope` requires
the login to match and the permissions to be no broader than the declared
capabilities. A token that carries ``admin`` or ``maintain`` — the ones that
merge, retarget branch protection, or change settings — is refused however it
was declared.
"""
from __future__ import annotations

import json
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .childenv import NEVER_PERMITTED, validate_env_name
from .commands import CommandRunner
from .errors import IdentityError

CAPABILITIES = frozenset({"push-branch", "comment-pr", "review-pr"})
BUILDER_CAPABILITIES = frozenset({"push-branch", "comment-pr"})
REVIEWER_CAPABILITIES = frozenset({"comment-pr", "review-pr"})

# The repository permissions that mean merge, branch-protection, or settings
# authority. No identity this module hands to a child may hold one.
FORBIDDEN_PERMISSIONS = ("admin", "maintain")

_LOGIN = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}(?:\[bot\])?\Z")
# Long enough to be a real credential, and with no whitespace: a token that
# fails this is far more likely to be a path, a placeholder, or a truncated
# read than a secret, and guessing which is exactly the ambiguity to refuse.
_MIN_TOKEN = 20


@dataclass(frozen=True)
class IdentitySpec:
    """One identity the launcher owns, as declared in the run configuration."""

    name: str
    login: str
    capabilities: frozenset[str]
    token_env: str | None = None
    token_file: Path | None = None
    inject_as: str = "GH_TOKEN"

    def __post_init__(self) -> None:
        if not _LOGIN.match(self.login):
            raise IdentityError(
                "identity login is not a usable GitHub login",
                evidence={"identity": self.name, "login": self.login},
            )
        unknown = sorted(self.capabilities - CAPABILITIES)
        if unknown:
            raise IdentityError(
                "identity declares a capability this launcher cannot grant; the "
                "vocabulary is closed and has no merge, approval, deploy, or admin form",
                evidence={
                    "identity": self.name,
                    "unknown": unknown,
                    "capabilities": sorted(CAPABILITIES),
                },
            )
        if not self.capabilities:
            raise IdentityError(
                "identity declares no capabilities", evidence={"identity": self.name}
            )
        if (self.token_env is None) == (self.token_file is None):
            raise IdentityError(
                "identity needs exactly one credential source: token_env or token_file",
                evidence={
                    "identity": self.name,
                    "token_env": self.token_env,
                    "token_file": str(self.token_file) if self.token_file else None,
                },
            )
        if self.token_env is not None:
            validate_env_name(self.token_env, what=f"identity {self.name} token_env")
        validate_env_name(self.inject_as, what=f"identity {self.name} inject_as")
        if self.inject_as.upper() in NEVER_PERMITTED:
            raise IdentityError(
                "identity cannot be injected under that variable name",
                evidence={"identity": self.name, "inject_as": self.inject_as},
            )

    @property
    def source_name(self) -> str:
        """Where the credential is read from, for evidence. Never the credential."""
        if self.token_env is not None:
            return f"env:{self.token_env}"
        return f"file:{self.token_file}"


@dataclass(frozen=True)
class ResolvedIdentity:
    """A spec plus the credential material, kept out of every rendered report."""

    spec: IdentitySpec
    _token: str = field(repr=False)

    @property
    def token(self) -> str:
        return self._token

    @property
    def login(self) -> str:
        return self.spec.login

    def injection(self) -> dict[str, str]:
        """The one credential variable this identity contributes to a child."""
        return {self.spec.inject_as: self._token}

    def as_evidence(self) -> dict[str, object]:
        """Everything about this identity that is safe to write down."""
        return {
            "identity": self.spec.name,
            "login": self.spec.login,
            "capabilities": sorted(self.spec.capabilities),
            "source": self.spec.source_name,
            "injected_as": self.spec.inject_as,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial, but it must never print a token
        return f"ResolvedIdentity(login={self.spec.login!r}, capabilities={sorted(self.spec.capabilities)})"


@dataclass(frozen=True)
class IdentityFacts:
    """What GitHub says a credential actually is and may do."""

    login: str
    permissions: Mapping[str, bool]


class IdentityVerifier(Protocol):
    """Injection seam for proving a credential is the identity it claims to be."""

    def facts(self, env: Mapping[str, str], *, repo: str) -> IdentityFacts: ...


def resolve(spec: IdentitySpec, parent_env: Mapping[str, str]) -> ResolvedIdentity:
    """Read the credential for ``spec``, or fail closed."""
    if spec.token_env is not None:
        raw = parent_env.get(spec.token_env)
        if raw is None:
            raise IdentityError(
                "the environment variable naming this identity's credential is not set",
                evidence={"identity": spec.name, "source": spec.source_name},
            )
        return ResolvedIdentity(spec=spec, _token=_checked_token(spec, raw))

    path = Path(spec.token_file or "").expanduser()
    try:
        info = path.stat()
    except OSError as exc:
        raise IdentityError(
            "this identity's credential file cannot be read",
            evidence={"identity": spec.name, "source": spec.source_name, "error": str(exc)},
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise IdentityError(
            "this identity's credential source is not a regular file",
            evidence={"identity": spec.name, "source": spec.source_name},
        )
    if info.st_mode & 0o077:
        raise IdentityError(
            "this identity's credential file is readable beyond its owner",
            evidence={
                "identity": spec.name,
                "source": spec.source_name,
                "mode": oct(info.st_mode & 0o777),
            },
        )
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - stat succeeded, read failed
        raise IdentityError(
            "this identity's credential file cannot be read",
            evidence={"identity": spec.name, "source": spec.source_name, "error": str(exc)},
        ) from exc
    return ResolvedIdentity(spec=spec, _token=_checked_token(spec, raw))


def _checked_token(spec: IdentitySpec, raw: str) -> str:
    """Reject anything that is not unambiguously one credential."""
    lines = [line for line in raw.splitlines() if line.strip()]
    if len(lines) != 1:
        raise IdentityError(
            "this identity's credential source does not hold exactly one credential",
            evidence={"identity": spec.name, "source": spec.source_name, "lines": len(lines)},
        )
    token = lines[0].strip()
    if len(token) < _MIN_TOKEN or any(character.isspace() for character in token):
        raise IdentityError(
            "this identity's credential is not a plausible token; refusing to guess",
            evidence={"identity": spec.name, "source": spec.source_name, "length": len(token)},
        )
    return token


def assert_scope(
    identity: ResolvedIdentity, facts: IdentityFacts, *, repo: str, lane: str
) -> None:
    """Require the credential to be this login, with no authority beyond its capabilities."""
    if facts.login.lower() != identity.login.lower():
        raise IdentityError(
            "the credential for this lane resolves to a different GitHub account",
            evidence={
                "lane": lane,
                "expected_login": identity.login,
                "actual_login": facts.login,
                "repo": repo,
            },
        )
    held = {name: bool(value) for name, value in facts.permissions.items()}
    forbidden = sorted(name for name in FORBIDDEN_PERMISSIONS if held.get(name))
    if forbidden:
        raise IdentityError(
            "this lane's credential holds repository authority that can merge or "
            "change protection; a child may never be given one",
            evidence={
                "lane": lane,
                "login": identity.login,
                "repo": repo,
                "forbidden_permissions": forbidden,
            },
        )
    wants_push = "push-branch" in identity.spec.capabilities
    if wants_push and not held.get("push"):
        raise IdentityError(
            "this lane's credential cannot push to the bound repository",
            evidence={"lane": lane, "login": identity.login, "repo": repo},
        )
    if not wants_push and held.get("push"):
        raise IdentityError(
            "this lane's credential can push but the identity declares no push capability",
            evidence={
                "lane": lane,
                "login": identity.login,
                "repo": repo,
                "capabilities": sorted(identity.spec.capabilities),
            },
        )
    if not held.get("pull"):
        raise IdentityError(
            "this lane's credential cannot read the bound repository",
            evidence={"lane": lane, "login": identity.login, "repo": repo},
        )


class GhIdentityVerifier:
    """Default verifier: ``gh api``, run with the child's own environment.

    Both calls use the environment the child is about to get, so what is
    verified is the credential the child will actually hold — not the
    operator's ambient ``gh`` login, which is precisely the authority this
    boundary exists to keep away from children.
    """

    def __init__(self, runner: CommandRunner, *, gh: str = "gh", timeout: float = 120.0) -> None:
        self._runner = runner
        self._gh = gh
        self._timeout = timeout

    def facts(self, env: Mapping[str, str], *, repo: str) -> IdentityFacts:
        login = self._text([self._gh, "api", "user", "--jq", ".login"], env=env, what="login")
        if not _LOGIN.match(login):
            raise IdentityError(
                "gh returned an unusable login for this credential",
                evidence={"repo": repo, "login": login[:80]},
            )
        raw = self._text(
            [self._gh, "api", f"repos/{repo}", "--jq", ".permissions"],
            env=env,
            what="repository permissions",
        )
        return IdentityFacts(login=login, permissions=_permissions(raw, repo=repo))

    def _text(self, argv: list[str], *, env: Mapping[str, str], what: str) -> str:
        result = self._runner.run(argv, env=env, timeout=self._timeout)
        if not result.ok:
            raise IdentityError(
                f"could not read the {what} for this lane's credential",
                evidence={"argv": list(argv), "returncode": result.returncode},
            )
        return (result.stdout or "").strip()


def _permissions(raw: str, *, repo: str) -> dict[str, bool]:
    try:
        payload = json.loads(raw or "null")
    except json.JSONDecodeError as exc:
        raise IdentityError(
            "gh returned unparsable repository permissions for this credential",
            evidence={"repo": repo, "error": str(exc)},
        ) from exc
    if not isinstance(payload, dict) or not payload:
        raise IdentityError(
            "gh reported no repository permissions for this credential",
            evidence={"repo": repo},
        )
    return {str(name): bool(value) for name, value in payload.items()}


__all__ = [
    "BUILDER_CAPABILITIES",
    "CAPABILITIES",
    "FORBIDDEN_PERMISSIONS",
    "REVIEWER_CAPABILITIES",
    "GhIdentityVerifier",
    "IdentityFacts",
    "IdentitySpec",
    "IdentityVerifier",
    "ResolvedIdentity",
    "assert_scope",
    "resolve",
]
