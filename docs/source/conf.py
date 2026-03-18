# Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License v3.
#
# See the LICENSE file for details.

# Configuration file for the Sphinx documentation builder.
# See https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# When building, autodoc imports src.app (and thus Streamlit). You may see
# Streamlit warnings ("No runtime found", "missing ScriptRunContext")—these
# are expected when the app is loaded outside "streamlit run" and can be ignored.

import os
import sys
from pathlib import Path
from typing import Any

# Add project root so that 'src' can be imported for autodoc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Give autodoc a safe, non-private runtime dataset when importing src.app.
os.environ.setdefault(
    "WCVA_DATASET_PATH",
    str(PROJECT_ROOT / "tests" / "fixtures" / "wcva_sample_dataset.csv"),
)
os.environ.setdefault(
    "WCVA_LA_CONTEXT_PATH",
    str(PROJECT_ROOT / "references" / "context" / "la_context_wales.csv"),
)

import src.eda as eda_module
import src.navigation as navigation_module
import src.section_pages.at_a_glance as at_a_glance_module
import src.section_pages.concerns_and_risks as concerns_module
import src.section_pages.data_notes as data_notes_module
import src.section_pages.demographics_and_types as demographics_module
import src.section_pages.deployment_health as deployment_health_module
import src.section_pages.earned_settlement as earned_settlement_module
import src.section_pages.executive_summary as executive_summary_module
import src.section_pages.overview as overview_module
import src.section_pages.sroi_references as sroi_module
import src.section_pages.trends_and_waves as trends_module
import src.section_pages.volunteer_recruitment as volunteer_recruitment_module
import src.section_pages.volunteer_retention as volunteer_retention_module
import src.section_pages.workforce_and_operations as workforce_module

navigation_module.render_sidebar_nav = lambda current_page=None: "Deployment Health"
eda_module.profile_summary = lambda df: {
    "has_volunteers_pct": 0.0,
    "has_paid_staff_pct": 0.0,
    "la_context": [],
}

for module_name in [
    at_a_glance_module,
    concerns_module,
    data_notes_module,
    demographics_module,
    deployment_health_module,
    earned_settlement_module,
    executive_summary_module,
    overview_module,
    sroi_module,
    trends_module,
    volunteer_recruitment_module,
    volunteer_retention_module,
    workforce_module,
]:
    for attr_name in dir(module_name):
        if attr_name.startswith("render_"):
            setattr(module_name, attr_name, lambda *args, **kwargs: None)

project = "Baromedr Cymru Wave 2 Dashboard"
copyright = "Bharadwaj Raman"
author = "Bharadwaj Raman - https://github.com/nba1990/"
release = "0.2.3"
version = "0.2"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "myst_parser",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns: Any = []

autosummary_generate = True

html_theme: str = "sphinx_rtd_theme"
html_static_path: Any = []
html_title = "Baromedr Cymru Wave 2 — Documentation"
html_short_title = "Baromedr W2"

# MyST (Markdown) configuration for docs under docs/source/.
myst_enable_extensions = [
    "colon_fence",
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# Autodoc (avoid duplicate object descriptions for dataclass attributes).
# Some dataclass fields (e.g. in src.config) may still emit harmless
# "duplicate object description" warnings when Sphinx imports the code;
# these do not affect the generated HTML and can be safely ignored.
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
# Source code available under AGPLv3: https://github.com/nba1990/wcva_data_analysis
