"""Repo-root pytest guard: Kernel-One tests run per service, never across services.

Why this file exists: all six services ship a test package named ``tests`` whose
``conftest.py`` prepends its own service root to ``sys.path`` (bare-import helper
convention). Collected in a single pytest process the packages collide —
ImportPathMismatchError / the wrong conftest wins. CI therefore runs one pytest
process per service (``python -m pytest tests/ -q`` from each service directory),
and so should you:

    One service:  cd services/<name> && python -m pytest tests/ -q
                  (or from the repo root: pytest services/<name>/tests)
    Repo-wide:    python scripts/run_tests.py   (CI-equivalent, per-service isolation)

What this guard does:

* A bare ``pytest`` at the repo root (or a path traversal that would wander into
  ``services/`` incidentally) collects nothing, prints the remedy once, and exits
  non-zero — no more pileup of 22 ImportPathMismatchError collection errors.
* Paths at or below ``services/<service>/tests`` are explicitly allowed, so
  pointing pytest at a single service's suite works from anywhere.
* Requesting two or more different services' suites in ONE process is rejected
  with a clean error — that combination is exactly the collision this file
  exists to prevent.

If a real root-level suite ever lands (docs/15 reserves tests/unit,
tests/integration, tests/security, tests/e2e), remove this guard in the same
change and give the root suite a unique package name.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REMEDY = (
    "\n[Kernel-One] pytest found nothing runnable at this level — and that is by design.\n"
    "Every service's suite lives at services/<service>/tests/ and must run in its own\n"
    "pytest process: all six ship a same-named `tests` package whose conftest.py prepends\n"
    "its service root to sys.path, so one process across services mixes them up.\n"
    "\n"
    "  One service:  cd services/<name> && python -m pytest tests/ -q\n"
    "                (or from the repo root: pytest services/<name>/tests)\n"
    "  Repo-wide:    python scripts/run_tests.py   (CI-equivalent, per-service isolation)\n"
)

_remedy_shown = False

# Top-level trees that must never be collected from a root-level run. `tests`
# covers a future root-level suite created before its author removes this guard.
_IGNORED_TOP_LEVEL = {
    "packages",
    "infra",
    "docs",
    "tests",
    ".freebuff",
    ".git",
    ".github",
    ".ruff_cache",
    ".pytest_cache",
}


def _rel_to_root(collection_path: Path, root: Path) -> Path | None:
    """Path relative to `root`, or None if outside it. Case-safe on Windows."""
    try:
        return Path(os.path.relpath(collection_path.resolve(), root))
    except (ValueError, OSError):
        return None


def pytest_ignore_collect(collection_path, config):
    global _remedy_shown
    rel = _rel_to_root(collection_path, config.rootpath)
    if rel is None:
        return None
    parts = rel.parts
    if parts and parts[0] == "services":
        # Allow only the services/<service>/tests subtree; ignore the rest so a
        # bare root run gathers nothing instead of colliding packages.
        if len(parts) >= 3 and parts[2] == "tests":
            return None
        if not _remedy_shown:
            _remedy_shown = True
            print(_REMEDY, file=sys.stderr)
        return True
    if parts and parts[0] in _IGNORED_TOP_LEVEL:
        return True
    return None


def pytest_configure(config):
    """Refuse multi-service collection up front with the remedy, not 22 errors."""
    requested: set[str] = set()
    for arg in config.args:
        path = Path(arg) if os.path.isabs(arg) else Path.cwd() / arg
        rel = _rel_to_root(path, config.rootpath / "services")
        if rel is None:
            continue
        parts = rel.parts
        if parts and not parts[0].startswith(".."):
            requested.add(parts[0])
    if len(requested) > 1:
        raise pytest.UsageError(
            "\n[Kernel-One] refusing to collect multiple services' suites in one\n"
            "pytest process (requested: %s).\n"
            "All six services ship a same-named `tests` package whose conftest.py\n"
            "prepends its service root to sys.path — one process across services\n"
            "mixes them up (ImportPathMismatchError).\n"
            "\n"
            "  One service:  cd services/<name> && python -m pytest tests/ -q\n"
            "  Repo-wide:    python scripts/run_tests.py   (one process per service)\n"
            % (", ".join(sorted(requested)),)
        )
