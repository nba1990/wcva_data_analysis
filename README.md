# WCVA Baromedr Cymru - Insight Data Analysis

Nearly 1/3 of adults in Wales volunteer, yet volunteer recruitment remains in the top three concerns for 30% of the organisations surveyed last year.

Data has been collected and anonymised from Baromedr Cymru – the quarterly temperature check for the Welsh voluntary sector in collaboration with Nottingham Trent University (NTU).

**Main Insight #1:**

> Baromedr Cymru dashboard can be access here: https://baromedr.cymru. From initial DevTools and HTML capture analysis, it looks like Baromedr Cymru is likely a Python Django server rendered template with static JavaScript enhancements rather than based on an SPA (Single Page Application) Framework. So far, no evidence has been found for the use of React, Vue, Next.js, visible API calls or large compiled JavaScript chunks.

Likely technology stack (rough):

```
Django view → template render → static JS enhances UI
```

Rationale 1:

```html
<!-- Local styles via Django static -->
<link rel="stylesheet" href=".../base.css">
<link rel="stylesheet" href=".../layout.css">
...
```

Rationale 2:

```html
<!-- Scripts -->
<script src=".../sidebar.js"></script>
<script src=".../shared.js"></script>
<script src=".../filters.js"></script>
<script src=".../summary.js"></script>
```

* “Local styles via Django static” comment
* Clean URL structure: `/summary/`, `/operations/`
* Each page loads a fresh HTML document (per your network screenshot)
* Page-specific JS (`summary.js`, `operations.js`)

## 🏗 Backend

* Python
* Django
* Server-rendered templates
* Likely Django ORM (Object Relational Mapping) querying database
* Static files served via Django static or reverse proxy

So far, no apparent sign of:

* Node backend
* FastAPI
* Separate API microservice

## 🗄 Data Layer (Most Likely)

* Filters are either:

  * Submitted via GET parameters
  * Or applied client-side after data is pre-embedded

Given the privacy rule (<5 suppression modal in the inspected HTML), it is far more likely that:

> Filtering is done server-side.

Which implies:

```
Qualtrics → ETL → Database (PostgreSQL likely)
Django view → filtered ORM query → aggregation → template context → render
```

* Compute percentages in backend
* Pass them into template
* Frontend just displays values and animations

For example in the HTML:

```html
<div class="metric-value" data-target="69">69%</div>
```

That number is already computed before render. There’s no JavaScript calculating it from raw rows.

## The Filtering System (Most Likely)

From the filter panel markup:

```html
<div class="filter-option" data-field="org_size" data-value="Small">
```

This appears to be a classic pattern:

* JavaScript collects selected filters
* Submits request (likely reload)
* Django reads GET parameters
* Applies filters to queryset
* Recomputes aggregations
* Renders new page

## The Privacy Threshold (<5 Rule) - Most Likely

Based on the modal in the HTML:

> “For privacy and data quality reasons, don’t display results when fewer than five organisations match the applied filters.”

```python
if queryset.count() < 5:
    context["suppress"] = True
```

Template then triggers warning modal possibly using k-anonymity at the application layer.


Possible Requirements:
* ETL from Qualtrics
* Writing aggregation logic
* QA on computed metrics
* Testing suppression logic
* Contributing to new features like Trends page
* Improving automation

### Apparent Strengths

* Clean UI
* Accessible filter logic
* Suppression rules implemented
* Clear modular CSS
* Separation of JavaScript per page
* Lightweight (very fast load times)


---

# Overview

Using exploratory data analysis and visual tools prepare a 5-minute presentation for WCVA’s executive team on the survey findings (using WCVA’s colour and branding schemes), focusing on the emerging challenges and opportunities for volunteer recruitment and retention, how organisations are approaching them, and where they may need support to inform policy across Wales.

Key goals:
- Perform exploratory data analysis (initial shallow + deep, if necessary)
- Build a rough plan of execution
- List possible high priority questions the policy teams might want to interrogate from such a dataset
- List emerging challenges and opportunities for volunteer recruitment and retention across the various organisations in the Voluntary sector in Wales
- Refine intial plan with results from the exploratory data analysis
- Build data-driven insights for the policy teams at WCVA and Welsh Government to help shape policy decisions to proactively help the Voluntary sector and alleviate some of the stress and pressure building up
- Ensure that the insights are pefectly grounded in data
- Ensure that the insights and visualisations (if any) are accessible and that they use the WCVA's colour palette and branding guidelines
- Distill some of the most influential insights (ranked in descending priority order) into an easily digestible 5-minute presentation with links to more detailed reports for later reference

---

# Features

- **Interactive Streamlit dashboard** with 8 pages: Overview, Volunteer Recruitment, Volunteer Retention, Workforce & Operations, Demographics & Types, Earned Settlement, Executive Summary, Data Notes
- **Dual-format executive presentation**: self-contained reveal.js HTML slide deck + structured PDF with bookmarks, TOC, and alt-text
- **WCVA branding** with switchable colour-blind-safe palette (sidebar toggle)
- **k-anonymity suppression** (results hidden when filtered sample < 5)
- **Accessibility**: redundant encoding on all charts, alt-text metadata, WCAG contrast validation
- **Per-chart export**: download PNG image or underlying CSV data table
- **12 high-priority policy questions** for policy team interrogation

---

# Project Structure

```
<project-root>/
│
├── src/
│   ├── __init__.py
│   ├── config.py              # WCVA palette, column mappings, response orderings, constants
│   ├── data_loader.py         # CSV loading, cleaning, derived columns, data quality profiling
│   ├── eda.py                 # Analytical functions (9 dimensions + executive highlights)
│   ├── charts.py              # WCVA-branded Plotly chart generators with accessibility
│   ├── app.py                 # Streamlit multi-page dashboard (8 pages)
│   └── generate_presentation.py  # Dual output: reveal.js HTML + fpdf2 PDF
│
├── datasets/
│   ├── WCVA_W2_Anonymised_Dataset.csv       # Wave 2 data (111 rows, 144 cols)
│   └── Baromedr_Cymru_QA_Response_Options.docx  # Questionnaire reference
│
├── output/
│   ├── presentation.html      # Self-contained HTML slide deck (opens in any browser)
│   └── presentation.pdf       # Structured PDF with TOC and bookmarks
│
├── plans/
│   └── policy_questions.md    # 12 high-priority policy questions
│
├── .streamlit/
│   └── config.toml            # WCVA-branded Streamlit theme
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

# Installation

```bash
git clone <repository-url>
cd <project-name>

# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

# Usage

### Interactive Dashboard

```bash
streamlit run src/app.py
```

Opens in your browser at `http://localhost:8501`. Use the sidebar to:
- Navigate between 8 pages
- Filter by organisation size, scope, and activity
- Toggle colour-blind friendly mode
- Download chart images and data tables

### Generate Executive Presentation

```bash
python -m src.generate_presentation
```

Produces two files in `output/`:
- `presentation.html` — self-contained reveal.js slide deck (email it, USB it, open in any browser)
- `presentation.pdf` — structured PDF with table of contents, bookmarks, and alt-text on images

---

# Configuration

All configuration is centralised in `src/config.py`:
- **WCVA brand palette** and colour-blind-safe alternative
- **Column-to-question mappings** from the Baromedr questionnaire
- **Response orderings** for consistent chart axes
- **Chart defaults** (font, sizing, margins)
- **k-anonymity threshold** (default: 5)
- **Wave 1 context** for cross-wave comparisons

The Streamlit theme is set in `.streamlit/config.toml`.

---

# Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard locally
streamlit run src/app.py

# Generate presentation outputs
python -m src.generate_presentation
```

---

# Testing

```bash
# Quick smoke test: verify all modules import and data loads
python -c "from src.data_loader import load_dataset; df = load_dataset(); print(f'OK: {df.shape}')"
```

---

# Roadmap

Possible planned improvements:

* [ ] Feature 1: Introduce API Layer
* [ ] Feature 2: Introduce Aggregation Tables
* [ ] Feature 3: Trend Computation Layer
* [ ] Feature 4: More Metadata Transparency

### Feature 1: Introduce API Layer

* Separate API endpoints
* Enable reuse for:

  * Embeddable widgets
  * WCVA internal dashboards
  * External research reuse

---

### Feature 2: Introduce Aggregation Tables

If not already done, precompute:

* Wave-level aggregates
* Filter-combination aggregates

This could improve performance and scalability.

---

### Feature 3: Trend Computation Layer

* Precomputed time-series tables
* Consistent denominator handling across waves
* Clear versioning of metrics

---

### Feature 4: More Metadata Transparency

Possibly add:

* Methodology link per metric
* Tooltip definitions
* Confidence interval explanation

---

# Contributing

Guidelines for contributions.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Submit a pull request

---

# License

GNU Affero General Public License v3.0 (AGPL v3.0)

Permissions of this strongest copyleft license are conditioned on making available complete source code of licensed works and modifications, which include larger works using a licensed work, under the same license. Copyright and license notices must be preserved. Contributors provide an express grant of patent rights. When a modified version is used to provide a service over a network, the complete source code of the modified version must be made available.

---

# Maintainers

* **Bharadwaj Raman** - Contact Email: maintainers@local.invalid
