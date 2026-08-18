"""Sphinx configuration for the options package."""

from __future__ import annotations

import os
import sys
from pathlib import Path

project = "options"
author = "Sachin"
copyright = "2026, Sachin"

# Add the source directory to the path so autodoc can find the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "tests"]

# Napoleon settings render Google-style docstrings.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# Autodoc settings.
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "show-module-summary": True,
    "member-order": "bysource",
}

# Render type hints as info blocks.
autodoc_typehints = "description"

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
