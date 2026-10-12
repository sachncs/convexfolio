"""Enforce package and critical-module coverage thresholds."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    """Read Coverage.py JSON output and enforce the release thresholds."""
    report_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("coverage.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    totals = report["totals"]
    errors: list[str] = []
    line_coverage = 100.0 * totals["covered_lines"] / totals["num_statements"]
    if line_coverage < 90.0:
        errors.append(f"package line coverage {line_coverage:.2f}% is below 90%")

    required_modules = {
        "convexfolio/backtest.py",
        "convexfolio/optimization.py",
        "convexfolio/config.py",
        "convexfolio/constraints.py",
        "convexfolio/validation.py",
    }
    for module in sorted(required_modules):
        summary = report["files"][module]["summary"]
        branches = summary["num_branches"]
        branch_coverage = (
            100.0 * summary["covered_branches"] / branches if branches else 100.0
        )
        if branch_coverage < 85.0:
            errors.append(
                f"{module} branch coverage {branch_coverage:.2f}% is below 85%"
            )

    if errors:
        for error in errors:
            print(f"coverage check: {error}", file=sys.stderr)
        return 1
    print(
        f"coverage check: package lines {line_coverage:.2f}%, "
        "critical branches passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
