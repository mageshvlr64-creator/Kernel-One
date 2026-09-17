#!/usr/bin/env python
"""Assemble the per-service CI test summary markdown posted on pull requests.

Consumes the artifacts downloaded by the `test-summary` job of ci.yml
(actions/download-artifact, pattern ``test-result-*``) — one directory per
artifact, each containing ``outcome.txt`` (the leg's job.status) and the
tool's output (``pytest-output.txt`` or ``ruff-output.txt``).

Prints the comment body to stdout: a hidden marker line (so the workflow can
find and update its own previous comment), a lint row, and one row per service
in CI matrix order with the pytest tail line parsed out. Missing artifacts
become "no result" rows rather than errors — a cancelled leg must not stop
the summary from posting.

Usage:
    python scripts/ci_test_summary.py <downloaded-artifacts-dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_tests  # sibling script; provides CI_MATRIX_ORDER

MARKER = "<!-- ci-per-service-test-summary -->"

OUTCOME_CELLS = {
    "success": "✅ pass",
    "failure": "❌ **fail**",
    "cancelled": "⚪ cancelled",
}

# pytest -q's tail, e.g. "93 passed, 2 warnings in 77.56s (0:01:17)"
# or "2 failed, 91 passed, 1 skipped in 12.34s".
TESTS_RE = re.compile(
    r"(?P<failed>\d+ failed)?[, ]*(?P<errors>\d+ errors?)?"
    r"[, ]*(?P<passed>\d+ passed)?[, ]*(?P<skipped>\d+ skipped)?"
    r" in (?P<time>\S+(?: \(\d+:\d+:\d+\))?)"
)


def _tail_line(text: str) -> str:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else "(no output captured)"


def _parse_tests(text: str) -> str:
    """Human 'N passed ... in Ts' from pytest's tail; raw tail if unparseable."""
    for line in reversed([ln.strip() for ln in text.strip().splitlines() if ln.strip()]):
        m = TESTS_RE.search(line)
        if m and (m.group("passed") or m.group("failed") or m.group("errors")):
            parts = [m.group(k) for k in ("failed", "errors", "passed", "skipped") if m.group(k)]
            return f"{', '.join(parts)} in {m.group('time')}"
    return _tail_line(text)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def main() -> int:
    # The table uses emoji/status glyphs; never let a cp1252 console crash us.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print("usage: ci_test_summary.py <artifacts-dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"artifacts dir not found: {root}", file=sys.stderr)
        return 2

    legs = [("lint (ruff F821,F841,E9)", "lint", "ruff-output.txt", _tail_line)]
    legs += [
        (f"tests — {service}", service, "pytest-output.txt", _parse_tests)
        for service in run_tests.CI_MATRIX_ORDER
    ]

    rows = []
    for label, artifact, output_name, parse in legs:
        leg_dir = root / f"test-result-{artifact}"
        outcome = (_read(leg_dir / "outcome.txt") or "").strip()
        output = _read(leg_dir / output_name)
        if output is not None:
            detail = parse(output)
        elif outcome:
            detail = "(no output captured — see job logs)"
        else:
            detail = "(artifact missing — job crashed before running)"
        outcome_cell = OUTCOME_CELLS.get(outcome, "⚠️ no result")
        rows.append(f"| {label} | {outcome_cell} | {detail} |")

    print(MARKER)
    print("## CI test summary — per service")
    print()
    print("| Suite | Outcome | Result |")
    print("|---|---|---|")
    for row in rows:
        print(row)
    print()
    if "❌" in "\n".join(rows):
        print("One or more legs failed — open this run's details for the full logs.")
    else:
        print("Full logs for each leg are in this workflow run's details.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
