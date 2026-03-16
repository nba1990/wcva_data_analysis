<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# ADR-005 – Docker and self-hosting support

## Context

The dashboard is deployed to Streamlit Community Cloud for managed hosting, but stakeholders may need to:

- Run the app on-premises or in a private cloud.
- Deploy to a container-based platform (e.g. Kubernetes, Cloud Run, ECS).
- Reproduce the same runtime environment locally or in CI.

A single, documented way to run the app in a container reduces environment drift and supports self-hosting and portability.

## Decision

We support **Docker** for containerised runs and self-hosting:

- **Dockerfile**: multi-stage not required; we use a single stage based on `python:3.12-slim`, install dependencies from `requirements.txt`, copy the app and assets, and run as a non-root user. Streamlit is configured to listen on `0.0.0.0:8501` inside the container.
- **docker-compose.yml**: one service that builds the image, maps port 8501, supports optional env (e.g. `WCVA_DEBUG_MEMORY`, `WCVA_DATASET_PATH`) and optional volume mounts for runtime data and `references/` so private datasets can be supplied without rebuilding.
- **Documentation**: `docs/DOCKER_AND_DEPLOYMENT.md` covers build/run commands, data and asset requirements, self-hosting with a reverse proxy, and basic security notes. README and ARCHITECTURE reference this guide.
- **Runtime health checks**: the app resolves runtime data sources at startup, falls back to the bundled sample fixture in explicit demo mode when the private dataset is unavailable, and exposes an in-app **Deployment Health** page so operators can quickly see whether datasets or optional reference assets are missing.

We do **not** change the app’s behaviour or configuration for Docker; the same code runs in local, Community Cloud, and container deployments. Private datasets are supplied at runtime via env vars, Streamlit secrets, or mounted files, while public reference assets can remain in the image.

## Consequences

- Teams can run the dashboard in Docker or Docker Compose with minimal extra setup.
- Self-hosting on a server is documented (reverse proxy, volumes, env vars).
- Hosted and self-hosted environments now fail more clearly when runtime data is missing, while still allowing demo-mode boot for smoke checks, docs builds, and first deploys.
- Container image can be used on Kubernetes, Cloud Run, or similar platforms; deployment details are left to the operator.
- Streamlit Community Cloud remains the primary managed option; Docker is an alternative for on-prem or custom cloud deployments.
