"""Validate static site invariants that do not require a Jekyll runtime."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class SiteParser(HTMLParser):
    """Collect accessibility and content invariants from the home template."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.tabs: dict[str, dict[str, str]] = {}
        self.panels: dict[str, dict[str, str]] = {}
        self.counters: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                raise ValueError(f"duplicate id: {element_id}")
            self.ids.add(element_id)
        if values.get("role") == "tab":
            tab_id = values.get("id")
            controls = values.get("aria-controls")
            if not tab_id or not controls:
                raise ValueError("every tab must have an id and aria-controls")
            self.tabs[tab_id] = values
        if values.get("role") == "tabpanel":
            panel_id = values.get("id")
            labelled_by = values.get("aria-labelledby")
            if not panel_id or not labelled_by:
                raise ValueError("every tabpanel must have an id and aria-labelledby")
            self.panels[panel_id] = values
        if "counter" in values.get("class", "").split():
            self.counters.append(values.get("data-to", ""))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    home = root / "site" / "_layouts" / "home.html"
    parser = SiteParser()
    parser.feed(home.read_text(encoding="utf-8"))

    errors: list[str] = []
    for tab_id, tab in parser.tabs.items():
        panel_id = tab["aria-controls"]
        if panel_id not in parser.panels:
            errors.append(f"{tab_id} controls missing panel {panel_id}")
        elif parser.panels[panel_id]["aria-labelledby"] != tab_id:
            errors.append(f"{panel_id} does not point back to {tab_id}")
    for panel_id, panel in parser.panels.items():
        if panel["aria-labelledby"] not in parser.tabs:
            errors.append(
                f"{panel_id} references missing tab {panel['aria-labelledby']}"
            )

    if parser.counters != ["3", "2", "100", "1"]:
        errors.append(f"unexpected no-JavaScript counter values: {parser.counters}")

    css = root / "site" / "assets" / "css" / "site.css"
    javascript = root / "site" / "assets" / "js" / "main.js"
    if not css.exists():
        errors.append("site stylesheet is missing")
    if not javascript.exists():
        errors.append("site JavaScript is missing")
    if re.search(r"Math\.random\s*\(", javascript.read_text(encoding="utf-8")):
        errors.append("site animation must not use nondeterministic Math.random")

    if errors:
        for error in errors:
            print(f"site check: {error}", file=sys.stderr)
        return 1
    print("site check: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
