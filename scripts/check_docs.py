"""Check repository and static-site links that resolve locally."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")
HTML_LINK = re.compile(r"\bhref=[\"']([^\"']+)[\"']")


def link_target(raw_target: str) -> str:
    """Remove optional Markdown titles and URL fragments from a target."""
    target = raw_target.strip().split(maxsplit=1)[0]
    return urlsplit(target).path


def candidate_paths(root: Path, source: Path, target: str) -> list[Path]:
    """Return possible source files for repository or Astro targets."""
    if target.startswith("/"):
        relative = target.lstrip("/")
        if relative.startswith("convexfolio/"):
            relative = relative.removeprefix("convexfolio/")
        if relative == "":
            return [root / "site" / "src" / "pages" / "index.astro"]
        if relative.startswith("docs/"):
            document = relative.removeprefix("docs/").strip("/") or "index"
            return [root / "site" / "src" / "content" / "docs" / f"{document}.md"]
        return [root / "site" / "src" / "pages" / relative]
    resolved = (source.parent / target).resolve()
    return [resolved]


def main() -> int:
    """Check local Markdown and HTML links."""
    root = Path(__file__).resolve().parents[1]
    sources = [root / "README.md", root / "CONTRIBUTING.md"]
    sources.extend((root / "site" / "src").rglob("*.md"))
    sources.extend((root / "site" / "src").rglob("*.html"))
    errors: list[str] = []
    for source in sources:
        text = source.read_text(encoding="utf-8")
        targets = MARKDOWN_LINK.findall(text) if source.suffix == ".md" else []
        targets += HTML_LINK.findall(text)
        for raw_target in targets:
            if raw_target.startswith(("http:", "https:", "mailto:", "//")):
                continue
            target = link_target(raw_target)
            if (
                not target
                or target.startswith("#")
                or "{{" in target
            ):
                continue
            candidates = candidate_paths(root, source, target)
            if not any(candidate.exists() for candidate in candidates):
                errors.append(f"{source.relative_to(root)} -> {raw_target}")

    if errors:
        for error in errors:
            print(f"docs check: missing local target {error}", file=sys.stderr)
        return 1
    print(f"docs check: checked {len(sources)} source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
