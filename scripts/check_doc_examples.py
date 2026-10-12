"""Compile every Python fenced block in the canonical documentation source."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def main() -> int:
    """Reject documentation examples that are no longer valid Python syntax."""
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    block_count = 0
    for path in sorted((root / "site" / "src" / "content" / "docs").rglob("*.md")):
        for block_number, block in enumerate(
            PYTHON_BLOCK.findall(path.read_text(encoding="utf-8")), start=1
        ):
            block_count += 1
            try:
                compile(block, f"{path}:{block_number}", "exec")
            except SyntaxError as exc:
                errors.append(f"{path.relative_to(root)} block {block_number}: {exc}")
    if errors:
        for error in errors:
            print(f"docs examples: {error}", file=sys.stderr)
        return 1
    print(f"docs examples: compiled {block_count} Python blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
