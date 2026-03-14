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
- **docker-compose.yml**: one service that builds the image, maps port 8501, supports optional env (e.g. `WCVA_DEBUG_MEMORY`) and optional volume mounts for `datasets/` and `references/` so data can be supplied at runtime without rebuilding.
- **Documentation**: `docs/DOCKER_AND_DEPLOYMENT.md` covers build/run commands, data and asset requirements, self-hosting with a reverse proxy, and basic security notes. README and ARCHITECTURE reference this guide.

We do **not** change the app’s behaviour or configuration for Docker; the same code runs in local, Community Cloud, and container deployments. Data and reference assets are either baked into the image at build time or mounted at run time.

## Consequences

- Teams can run the dashboard in Docker or Docker Compose with minimal extra setup.
- Self-hosting on a server is documented (reverse proxy, volumes, env vars).
- Container image can be used on Kubernetes, Cloud Run, or similar platforms; deployment details are left to the operator.
- Streamlit Community Cloud remains the primary managed option; Docker is an alternative for on-prem or custom cloud deployments.
