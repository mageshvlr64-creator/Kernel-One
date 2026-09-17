#!/usr/bin/env python
"""Developer preflight: CI's ruff gate plus only the suites your changes can affect.

Runs the two things CI will do to a push — the ruff error gate and the per-service
pytest suites — before you commit, but skips suites no uncommitted file can affect.
Suite isolation matches CI exactly (one pytest process per service) because the
runs are delegated to scripts/run_tests.py.

Selection rules for uncommitted changes (staged, unstaged, and untracked):
- files under services/<name>/...      -> that service's suite
- conftest.py, pytest.ini, scripts/... -> all suites (they change how any suite
  is discovered or run, so run everything)
- docs/, README.md, CHANGELOG.md, ...  -> no suite
- no uncommitted changes at all        -> ruff only

Usage:
    python scripts/preflight.py              # ruff + affected suites
    python scripts/preflight.py --dry-run    # show the selection, run no suites
    python scripts/preflight.py --fail-fast  # stop at the first failing suite
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_tests  # noqa: E402  (sibling script; provides the CI constants)

# Exactly CI's lint gate (.github/workflows/ci.yml, "Static checks" job).
RUFF_CMD = [sys.executable, "-m", "ruff", "check", "services/", "--select", "F821,F841,E9"]

# Files whose change can affect every suite's discovery/execution.
GLOBAL_HINTS = ("conftest.py", "pytest.ini", "scripts/")

GIT_TIMEOUT_SECONDS = 60
RUFF_TIMEOUT_SECONDS = 120


def _run_bounded(cmd: list[str], timeout: int) -> subprocess.CompletedProcess | None:
    """subprocess.run with a timeout and one retry (git/ruff can wedge on slow
    network filesystems — OneDrive in particular). None means unusably wedged."""
    for attempt in (1, 2):
        try:
            return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, check=False,
                                  timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"preflight: {' '.join(cmd[:3])} timed out (attempt {attempt}/2)",
                  file=sys.stderr)
        except OSError as exc:
            print(f"preflight: cannot run {cmd[0]}: {exc}", file=sys.stderr)
            return None
    return None

def uncommitted_paths() -> list[str] | None:
    """Staged + unstaged + untracked files (gitignore respected), or None on git failure."""
    commands = (
        ["git", "diff", "--name-only", "-z", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths: list[str] = []
    for cmd in commands:
        proc = _run_bounded(cmd, GIT_TIMEOUT_SECONDS)
        if proc is None:
            return None
        if proc.returncode != 0:
            detail = (proc.stderr or b"").decode("utf-8", "replace").strip()
            print(f"preflight: git failed: {detail}", file=sys.stderr)
            return None
        paths.extend(p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p)
    return paths


def select_suites(paths: list[str]) -> tuple[list[str], list[str], list[str], int]:
    """Map changed files to suites.

    Returns (suites in CI matrix order, per-service evidence lines, global-file
    lines, count of files that touch no suite).
    """
    available = set(run_tests.discover_services())
    per_service: dict[str, list[str]] = {}
    global_files: list[str] = []
    no_effect = 0
    for raw in paths:
        norm = raw.replace("\\", "/")
        parts = norm.split("/")
        if parts[0] == "services" and len(parts) > 1 and parts[1] in available:
            per_service.setdefault(parts[1], []).append(norm)
        elif norm.startswith(GLOBAL_HINTS):
            global_files.append(norm)
        else:
            no_effect += 1
    if global_files:
        suites = [s for s in run_tests.CI_MATRIX_ORDER if s in available]
        evidence = [
            f"  {service}: forced by {len(global_files)} file(s) outside any single"
            f" service ({global_files[0]}{',' if len(global_files) > 1 else ''} ...)"
            for service in suites
        ]
    else:
        suites = [s for s in run_tests.CI_MATRIX_ORDER if s in per_service]
        evidence = [f"  {s}: {len(per_service[s])} file(s)" for s in suites]
    return suites, evidence, global_files, no_effect


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preflight: CI's ruff gate plus only the affected test suites.",
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="stop at the first failing suite"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the suite selection without running the suites",
    )
    args = parser.parse_args()

    paths = uncommitted_paths()
    if paths is None:
        return 2

    print("== ruff (CI scope: services/ --select F821,F841,E9) ==", flush=True)
    ruff = _run_bounded(RUFF_CMD, RUFF_TIMEOUT_SECONDS)
    if ruff is None:
        print("\npreflight: ruff could not run (repeated timeouts) — not a lint failure.",
              file=sys.stderr)
        return 2
    sys.stdout.write(ruff.stdout.decode("utf-8", "replace"))
    if ruff.returncode != 0:
        print(
            "\npreflight: ruff failed — fix the errors above before committing.",
            file=sys.stderr,
        )
        return 1
    print("ruff: clean", flush=True)

    if not paths:
        print("preflight: no uncommitted changes — nothing to test.")
        return 0

    suites, evidence, global_files, no_effect = select_suites(paths)
    print("\n== suite selection from uncommitted changes ==")
    for line in evidence:
        print(line)
    if no_effect:
        print(f"  ({no_effect} file(s) touch no suite: docs, README, CHANGELOG, ...)")

    if args.dry_run:
        print(f"\ndry-run: would run {len(suites)} suite(s) via scripts/run_tests.py")
        return 0
    if not suites:
        print("preflight: no suite is affected — skipping tests.")
        return 0

    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_tests.py"), *suites]
    if args.fail_fast:
        cmd.append("--fail-fast")
    sys.stdout.flush()  # the child writes straight to the fd; keep report order sane
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
