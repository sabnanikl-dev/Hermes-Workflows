"""Keep captured child output useful as evidence without carrying secrets.

Reviewer, builder, and gate output is untrusted and may echo tokens from the
environment. Everything that reaches a report or an error's evidence mapping
goes through :func:`scrub` first, then :func:`clip` so a runaway log cannot
bury the parts that matter.

:func:`scrub` and :func:`evidence` only handle text, so a value that reaches a
report nested inside a dict, list, or tuple — an argv array, a git status
mapping, a lockfile body attached whole — can slip past the call site that was
supposed to redact it. :func:`sanitize` is the final boundary: it walks a whole
evidence structure recursively and scrubs every string in it, keys included,
while leaving the structure and the non-string scalar types intact.
"""
from __future__ import annotations

import re
from typing import Any

PLACEHOLDER = "<redacted>"

_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    # GitHub tokens: gho_/ghp_/ghu_/ghs_/ghr_ and fine-grained PATs.
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), PLACEHOLDER),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), PLACEHOLDER),
    # Provider-style keys.
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"), PLACEHOLDER),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), PLACEHOLDER),
    (re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}"), PLACEHOLDER),
    # Authorization headers.
    (re.compile(r"(?i)\b(authorization\s*:\s*)(bearer|token|basic)\s+\S+"), r"\1\2 " + PLACEHOLDER),
    (re.compile(r"(?i)\b(bearer|token)\s+[A-Za-z0-9._\-]{12,}"), r"\1 " + PLACEHOLDER),
    # Anything named like a credential in KEY=value or KEY: value shape.
    (
        re.compile(
            r"(?i)\b([A-Za-z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|APIKEY|API_KEY|CREDENTIAL|PRIVATE_KEY)[A-Za-z0-9_]*)"
            r"(\s*[=:]\s*)(?!\s)\S+"
        ),
        r"\1\2" + PLACEHOLDER,
    ),
    # URLs carrying inline basic-auth credentials.
    (re.compile(r"\b([a-zA-Z][a-zA-Z0-9+.\-]*://)[^\s/:@]+:[^\s/@]+@"), r"\1" + PLACEHOLDER + "@"),
    # PEM blocks.
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
        PLACEHOLDER,
    ),
)


def scrub(text: str) -> str:
    """Replace credential-shaped substrings with a fixed placeholder."""
    if not text:
        return ""
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    return text


def clip(text: str, *, limit: int = 4000) -> str:
    """Keep the head and the tail of long output; machine markers live at the tail."""
    if limit < 80:
        raise ValueError("limit must leave room for both ends")
    if len(text) <= limit:
        return text
    keep = (limit - 40) // 2
    dropped = len(text) - (2 * keep)
    return f"{text[:keep]}\n... [{dropped} characters elided] ...\n{text[-keep:]}"


def evidence(text: str, *, limit: int = 4000) -> str:
    """Scrub then clip, in that order, for anything stored as run evidence."""
    return clip(scrub(text), limit=limit)


MAX_DEPTH = 12
_TOO_DEEP = "<elided: evidence nested deeper than the sanitizer walks>"
_CYCLE = "<elided: circular evidence reference>"


def sanitize(
    value: Any,
    *,
    limit: int = 4000,
    _depth: int = 0,
    _seen: frozenset[int] = frozenset(),
) -> Any:
    """Recursively scrub every string in an evidence structure.

    This is the final serialization boundary: no value reaches JSON or Markdown
    without passing through it, however deeply a caller nested it. Structure and
    non-string scalar types survive — a mapping stays a mapping, a list stays a
    list, a tuple stays a tuple, and ``int``/``float``/``bool``/``None`` are
    returned unchanged — so the report is still readable and machine-usable
    rather than one blindly stringified blob.

    Depth and identity are bounded: a structure deeper than :data:`MAX_DEPTH` or
    one that refers back to itself is replaced with a marker instead of being
    walked forever.
    """
    if isinstance(value, str):
        return evidence(value, limit=limit)
    if value is None or isinstance(value, (bool, int, float)):
        # bool is checked with int on purpose: both are safe to pass through.
        return value
    if isinstance(value, (dict, list, tuple, set, frozenset)):
        if _depth >= MAX_DEPTH:
            return _TOO_DEEP
        if id(value) in _seen:
            return _CYCLE
        seen = _seen | {id(value)}
        deeper = {"limit": limit, "_depth": _depth + 1, "_seen": seen}
        if isinstance(value, dict):
            # Keys are evidence too: an env-var name can carry the secret's shape.
            return {
                evidence(key if isinstance(key, str) else str(key), limit=limit): sanitize(
                    item, **deeper
                )
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(sanitize(item, **deeper) for item in value)
        if isinstance(value, list):
            return [sanitize(item, **deeper) for item in value]
        # Sets have no JSON form; render them as a stable list.
        return [sanitize(item, **deeper) for item in sorted(value, key=repr)]
    # Anything else (a Path, a dataclass, an exception) has no safe structural
    # form here, so it is rendered as text and scrubbed like text.
    return evidence(str(value), limit=limit)


__all__ = ["MAX_DEPTH", "PLACEHOLDER", "clip", "evidence", "sanitize", "scrub"]
