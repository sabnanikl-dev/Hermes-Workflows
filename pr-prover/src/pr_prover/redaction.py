"""Keep captured child output useful as evidence without carrying secrets.

Reviewer, builder, and gate output is untrusted and may echo tokens from the
environment. Everything that reaches a report or an error's evidence mapping
goes through :func:`scrub` first, then :func:`clip` so a runaway log cannot
bury the parts that matter.
"""
from __future__ import annotations

import re

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
