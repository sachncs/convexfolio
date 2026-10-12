"""Validate that the repository's release metadata describes one version."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


def check_release_metadata(root: Path) -> list[str]:
    """Return actionable errors for inconsistent release metadata.

    Args:
        root: Repository root containing ``pyproject.toml``.

    Returns:
        A list of validation errors. An empty list means the metadata agrees.
    """
    pyproject = root / "pyproject.toml"
    with pyproject.open("rb") as handle:
        version = str(tomllib.load(handle)["project"]["version"])
    errors: list[str] = []

    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    citation_match = re.search(
        r"^version:\s*[\"']([^\"']+)[\"']\s*$", citation, re.MULTILINE
    )
    if citation_match is None or citation_match.group(1) != version:
        errors.append("CITATION.cff version does not match pyproject.toml")

    readme = (root / "README.md").read_text(encoding="utf-8")
    wheel_url = (
        f"releases/download/v{version}/convexfolio-{version}-py3-none-any.whl"
    )
    if wheel_url not in readme:
        errors.append("README.md does not point at the current release wheel")

    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}] - " not in changelog:
        errors.append("CHANGELOG.md has no dated section for the current version")
    if f"[{version}]:" not in changelog:
        errors.append("CHANGELOG.md has no comparison link for the current version")

    release_doc = (
        root / "site" / "src" / "content" / "docs" / "release.md"
    ).read_text(encoding="utf-8")
    if f"git tag v{version}" not in release_doc:
        errors.append("release guide does not show the current release tag")
    if "npm ci && npm run check && npm run build" not in release_doc:
        errors.append("release guide is missing the Astro build gate")
    return errors


def main() -> int:
    """Run release metadata validation from the repository root."""
    errors = check_release_metadata(Path(__file__).resolve().parents[1])
    if errors:
        for error in errors:
            print(f"release check: {error}", file=sys.stderr)
        return 1
    print("release check: metadata is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
