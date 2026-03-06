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

# Features [WIP]

- Feature 1
- Feature 2
- Feature 3

---

# Project Structure

```

<project-root>/
│
├── src/            # Source code
├── tests/          # Test files
├── datasets/       # Datasets for the analysis
├── plans/          # Work plans and any other project / programme management related artefacts
├── docs/           # Documentation
├── scripts/        # Utility scripts
├── config/         # Configuration files
└── README.md
└── LICENSE

````

---

# Installation [WIP]

```bash
git clone <repository-url>
cd <project-name>
<installation-steps>
````

Example:

```bash
npm install
```

or

```bash
pip install -r requirements.txt
```

---

# Usage [WIP]

Example usage:

```bash
<run-command>
```

Example:

```bash
npm start
```

or

```bash
python main.py
```

---

# Configuration [WIP]

Explain configuration options.

Example:

```
ENV_VAR_NAME=value
```

---

# Development [WIP]

Steps for contributors:

```bash
# install dependencies
<install-command>

# run development environment
<dev-command>

# run tests
<test-command>
```

---

# Testing [WIP]

Explain how tests are run.

```bash
<test-command>
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
