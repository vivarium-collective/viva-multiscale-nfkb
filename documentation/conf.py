"""Sphinx configuration for the viva-multiscale-nfkb documentation.

Build locally:  uv run --group docs sphinx-build -W -b html documentation documentation/_build/html
Read the Docs builds it from .readthedocs.yaml at the repository root.
"""

project = "viva-multiscale-nfkb"
author = "vivarium-collective"
copyright = "2026, vivarium-collective"
release = "0.0.0"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.mathjax",
]

myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence", "deflist", "attrs_inline"]
myst_heading_anchors = 3
source_suffix = {".md": "markdown"}
exclude_patterns = ["_build"]

html_theme = "pydata_sphinx_theme"
html_title = "viva-multiscale-nfkb"
html_static_path = ["_static"]
# The workspace logo (assets/logos/logo.svg) is the header on every page and the favicon.
html_logo = "../assets/logos/logo.svg"
html_favicon = "../assets/logos/logo.svg"
html_css_files = ["colors.css"]
html_context = {"default_mode": "dark"}
html_theme_options = {
    "github_url": "https://github.com/vivarium-collective/viva-multiscale-nfkb",
    "navigation_with_keys": False,
    "show_toc_level": 2,
    "navbar_align": "left",
    "logo": {"text": "viva-multiscale-nfkb", "alt_text": "viva-multiscale-nfkb"},
}

# Source links in the pages point at the repository on GitHub.
REPO = "https://github.com/vivarium-collective/viva-multiscale-nfkb/blob/main"
myst_substitutions = {"repo": REPO}
