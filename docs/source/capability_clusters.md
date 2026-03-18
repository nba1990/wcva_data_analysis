---
title: Capability clusters (PaaS/SaaS and product engineering)
---

# Capability clusters (PaaS/SaaS and product engineering)

This page distils `scratch/capability_clusters_paas_saas_chat_transcript.md` into a **high-signal, low-noise** capability model.

It is:

- **general-purpose** (applies to most software products),
- **explicitly linked** to this repository (so it is not abstract), and
- kept **proportionate** (use it as a map, not as a demand to build everything).

## The 12 umbrella clusters

Use these clusters to structure reviews, roadmaps, ADRs, or readiness checklists.

1) **Product_and_strategy**: who it serves, why it exists, and what success looks like.
2) **User_experience_and_adoption**: UX, accessibility, content, information architecture, and change adoption.
3) **Functional_capabilities**: the core business features and workflows.
4) **Architecture_and_engineering**: modularity, maintainability, extensibility, and technical debt management.
5) **Data_and_integration**: modelling, quality, lifecycle, imports/exports, APIs, and interoperability.
6) **Security_privacy_and_trust**: IAM, secrets, encryption, auditability, privacy, and abuse prevention.
7) **Reliability_performance_and_scalability**: availability, resilience, performance, and capacity.
8) **Observability_operations_and_service_management**: logs/metrics/traces, runbooks, incident/problem management, operability.
9) **Platform_infrastructure_and_delivery**: infrastructure, environments, CI/CD, deployment strategy, rollback.
10) **Quality_governance_and_compliance**: testing strategy, assurance evidence, risk and compliance controls.
11) **Developer_enablement_and_ways_of_working**: DevEx, onboarding, conventions, internal tooling, knowledge management.
12) **Commercial_customer_and_org_success**: support model, customer success, cost management, vendor management (where relevant).

## Mapping from the source transcript

The source transcript contains a longer, more granular list (for example splitting “observability” into logging/metrics/tracing, and “delivery” into CI/CD/release management/change management).

For this repo, the umbrella model above is the deliberately de-duplicated view. You can map from the transcript into umbrellas as follows:

- **Product_and_strategy**: “Product and business”, “Adoption/change/organisational fit”, “Intelligence/insight/learning”.
- **User_experience_and_adoption**: “User experience and interaction”, plus adoption/change aspects that are user-facing.
- **Functional_capabilities**: “Functional capabilities”, “Workflow and process support”, “Reporting and analytics”, “Automation”.
- **Architecture_and_engineering**: “Architecture and engineering”, “Modularity”, “Maintainability”, “Dependency/config management”.
- **Data_and_integration**: “Data and information management”, “Integration and interoperability”.
- **Security_privacy_and_trust**: “Security, privacy, and trust”.
- **Reliability_performance_and_scalability**: “Reliability/resilience/continuity” + “Performance and scalability”.
- **Observability_operations_and_service_management**: “Observability and operability” + “Operations and service management”.
- **Platform_infrastructure_and_delivery**: “Platform/infrastructure/runtime” + “Delivery and change management”.
- **Quality_governance_and_compliance**: “Quality and assurance” + “Governance/risk/compliance”.
- **Developer_enablement_and_ways_of_working**: “Developer experience and internal enablement”.
- **Commercial_customer_and_org_success**: “Financial and commercial operations” + “Customer success and external relationship management”.

## How this repository maps to the clusters (concrete links)

This repo is a Streamlit dashboard with a strong “operate it safely” posture. Examples by cluster:

- **Architecture_and_engineering**
  - High-level flow and module boundaries: `ARCHITECTURE.md`, Sphinx `architecture`.
  - Architecture decisions: `docs/adr/ADR-00*.md`.
  - Import-linter architecture contracts: `.importlinter`, Sphinx `architecture/contracts`.

- **Data_and_integration**
  - Runtime data resolution (path/URL, demo fallback): `src/config.py`, `src/data_loader.py`.
  - Cross-wave registry and schema mapping direction: `src/wave_context.py`, `src/wave_schema.py`, ADR-008.

- **Security_privacy_and_trust**
  - URL masking for diagnostics/logs: `src/config.py:mask_runtime_value`.
  - k-anonymity suppression contract: `K_ANON_THRESHOLD` and page gating in `src/app.py` and `src/section_pages/*`.
  - Secrets/demo-mode guidance: `docs/learning/02_private_data_secrets_and_demo_mode.md`, ADR-007.

- **Observability_operations_and_service_management**
  - In-app diagnostics: `src/section_pages/deployment_health.py`.
  - Operator guidance: `docs/source/operations_runbook.rst`, `docs/source/deployment_checklist.md`.

- **Platform_infrastructure_and_delivery**
  - CI is the contract: `.github/workflows/ci.yml`, ADR-006.
  - Docker/self-hosting: `docs/DOCKER_AND_DEPLOYMENT.md`, ADR-005.
  - Read the Docs build: `.readthedocs.yaml`, `docs/source/conf.py`.

- **Quality_governance_and_compliance**
  - Unit/integration/property tests: `tests/` (notably `tests/unit/test_eda_properties.py`).
  - Dependency security audit in CI: `.github/workflows/ci.yml` (`pip-audit` job).

- **Developer_enablement_and_ways_of_working**
  - Contribution workflow: `CONTRIBUTING.md`.
  - Learning guides: `docs/learning/`.
  - Release discipline (canonical runbook): Sphinx `release_process`.

## How to use the clusters (without over-engineering)

Use the model as a **lens**, not as a mandate:

- **For reviews**: “What clusters does this change touch? What could go wrong there?”
- **For roadmaps**: “Which 1–2 clusters are the current bottleneck?”
- **For documentation**: “Where is the single source of truth for each cluster we care about?”

If you are building a small internal app, you may treat many clusters as “minimal maturity” (basic checklists and a couple of tests). For a public-facing or regulated environment, you will deepen the clusters that carry the highest risk.
