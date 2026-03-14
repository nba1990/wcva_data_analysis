# Configuration file for the Sphinx documentation builder.
# See https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# When building, autodoc imports src.app (and thus Streamlit). You may see
# Streamlit warnings ("No runtime found", "missing ScriptRunContext")—these
# are expected when the app is loaded outside "streamlit run" and can be ignored.

import os
import sys
from typing import Any

# Add project root so that 'src' can be imported for autodoc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

project = "Baromedr Cymru Wave 2 Dashboard"
copyright = "Bharadwaj Raman"
author = "Bharadwaj Raman - https://github.com/nba1990/"
release = "0.2.1"
version = "0.2"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns: Any = []

html_theme: str = "sphinx_rtd_theme"
html_static_path: Any = []
html_title = "Baromedr Cymru Wave 2 — Documentation"
html_short_title = "Baromedr W2"

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# Autodoc (avoid duplicate object descriptions for dataclass attributes)
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": False,
    "show-inheritance": True,
    "special-members": False,
}
autodoc_preserve_defaults = True
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Intersphinx for Python and pandas (streamlit objects.inv often missing, so omitted)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}
