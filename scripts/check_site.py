"""Validate source invariants for the Astro documentation site."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    """Check the Astro source tree and reject stale Jekyll structure."""
    root = Path(__file__).resolve().parents[1]
    site = root / "site"
    errors: list[str] = []
    required = (
        site / "astro.config.mjs",
        site / "package.json",
        site / "package-lock.json",
        site / "src" / "content.config.ts",
        site / "src" / "pages" / "index.astro",
        site / "src" / "pages" / "docs" / "[...slug].astro",
    )
    for path in required:
        if not path.exists():
            errors.append(f"missing Astro file: {path.relative_to(root)}")

    forbidden = (
        site / "_config.yml",
        site / "_layouts",
        site / "_includes",
        site / "Gemfile",
        site / "Gemfile.lock",
        site / "docs",
    )
    for path in forbidden:
        if path.exists():
            errors.append(f"stale Jekyll/source duplicate: {path.relative_to(root)}")

    homepage = site / "src" / "pages" / "index.astro"
    stylesheet = site / "public" / "site.css"
    if homepage.exists():
        text = homepage.read_text(encoding="utf-8").lower()
        for phrase in ("production ready", "lowest risk", "exact"):
            if phrase in text:
                errors.append(f"homepage contains an unqualified claim: {phrase}")
        homepage_text = homepage.read_text(encoding="utf-8")
        for marker in ('id="solver-demo"', 'aria-live="polite"', "<noscript>"):
            if marker not in homepage_text:
                errors.append(
                    f"homepage is missing accessibility/fallback marker: {marker}"
                )
    if stylesheet.exists():
        css_text = stylesheet.read_text(encoding="utf-8")
        for marker in (":focus-visible", "prefers-reduced-motion", "max-width: 760px"):
            if marker not in css_text:
                errors.append(
                    f"stylesheet is missing responsive/accessibility marker: {marker}"
                )

    if errors:
        for error in errors:
            print(f"site check: {error}", file=sys.stderr)
        return 1
    print("site check: Astro source checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
