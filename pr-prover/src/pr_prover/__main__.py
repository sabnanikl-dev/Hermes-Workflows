"""Allow ``python3 -m pr_prover`` alongside the ``pr-prover`` entry point."""
from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
