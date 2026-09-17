#!/usr/bin/env python
"""Run Kernel-One's test suites the way CI does: one pytest process per service.

Why per-service processes? Every service's test package is named ``tests`` and each
``tests/conftest.py`` prepends its own service root to ``sys.path``, so a single
pytest process collecting across services mixes the packages up (see the root
``pytest.ini`` / ``conftest.py`` guard for the full story). This runner reproduces
CI's isolation (``python -m pytest tests/ -q`` from each service directory) and
prints a per-service summary; it exits non-zero if any suite fails.

Usage:
    python scripts/run_tests.py                      # all services, CI matrix order
    python scripts/run_tests.py evidence-service     # subset by name
    python scripts/run_tests.py --fail-fast          # stop at the first failing suite
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"

# Mirrors the `matrix.service` order in .github/workflows/ci.yml.
CI_MATRIX_ORDER = [
    "document-pipeline",
    "model-router",
    "inference-gateway",
    "industrial-service",
    "knowledge-fabric",
    "evidence-service",
]

# Same invocation as CI's "Run test suite" step.
PYTEST_CMD = [sys.executable, "-m", "pytest", "tests/", "-q"]

TAIL_LINES_ON_SUCCESS = 6
PER_SUITE_TIMEOUT_SECONDS = 900


def discover_services() -> list[str]:
    """Services with a tests/ directory, as a safety net if the matrix drifts."""
    return sorted(
        entry.name
        for entry in SERVICES_DIR.iterdir()
        if entry.is_dir() and (entry / "tests").is_dir()
    )


def run_suite(service: str) -> tuple[int, str]:
    """Run one service's suite, returning (exit code, combined output)."""
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            PYTEST_CMD,
            cwd=SERVICES_DIR / service,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PER_SUITE_TIMEOUT_SECONDS,
            check=False,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {PER_SUITE_TIMEOUT_SECONDS}s\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run each service's test suite in its own pytest process (CI-equivalent).",
    )
    parser.add_argument(
        "services",
        nargs="*",
        help="subset of services to run (default: all, in CI matrix order)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop at the first failing suite",
    )
    args = parser.parse_args()

    available = discover_services()
    if args.services:
        unknown = [name for name in args.services if name not in available]
        if unknown:
            parser.error(
                "unknown service(s): %s (available: %s)"
                % (", ".join(unknown), ", ".join(available))
            )
        selected = args.services
    else:
        selected = [name for name in CI_MATRIX_ORDER if name in available]

    results: list[tuple[str, int]] = []
    for service in selected:
        print(f"\n=== {service} ===", flush=True)
        code, output = run_suite(service)
        if code == 0:
            tail = "\n".join(output.strip().splitlines()[-TAIL_LINES_ON_SUCCESS:])
            print(tail, flush=True)
        else:
            # Full output on failure: the failure details are above the summary line.
            print(output.rstrip(), flush=True)
        results.append((service, code))
        if code != 0 and args.fail_fast:
            break

    print("\n=== Summary ===")
    for service, code in results:
        print(f"  {service}: {'PASS' if code == 0 else f'FAIL (exit {code})'}")

    failures = [service for service, code in results if code != 0]
    if failures:
        print(
            "\nFailing suite output is printed above its heading. Re-run one suite:\n"
            "  python scripts/run_tests.py %s" % failures[0]
        )
        return 1
    print(f"\nAll {len(results)} service suite(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
