<!--
Copyright (C) 2026 - Bharadwaj Raman - https://github.com/nba1990/
SPDX-License-Identifier: AGPL-3.0-or-later
See the LICENSE file for full licensing terms.
-->

# Docker and deployment guide

This document describes how to run the WCVA Baromedr Cymru Wave 2 Dashboard in Docker and how to self-host or deploy it on a server or cloud.

---

## Prerequisites

- **Docker** (Engine 20.10+) and **Docker Compose** (v2+), or a compatible container runtime (Podman, etc.).
- Access to the **private Wave 2 dataset** and any **reference assets** (see [Data and assets](#data-and-assets) below).

---

## Quick start with Docker Compose

From the project root:

```bash
# Build and run in the background
docker compose up -d

# Or build and run in the foreground (logs in terminal)
docker compose up --build
```

Then open **http://localhost:8501** in your browser.

To stop:

```bash
docker compose down
```

---

## Building and running with Docker only

### Build the image

```bash
docker build -t wcva-baromedr-dashboard:latest .
```

### Run the container

```bash
docker run -d \
  --name wcva-baromedr-dashboard \
  -p 8501:8501 \
  wcva-baromedr-dashboard:latest
```

Open **http://localhost:8501**. To stop and remove the container:

```bash
docker stop wcva-baromedr-dashboard
docker rm wcva-baromedr-dashboard
```

### Optional: enable debug memory display

To show process memory usage in the sidebar (for tuning or debugging):

```bash
docker run -d \
  --name wcva-baromedr-dashboard \
  -p 8501:8501 \
  -e WCVA_DEBUG_MEMORY=1 \
  wcva-baromedr-dashboard:latest
```

With Compose, set the env in your shell before `up`, or in a `.env` file:

```bash
export WCVA_DEBUG_MEMORY=1
docker compose up -d
```

---

## Data and assets

The app expects:

1. **Wave 2 dataset source** — required. Configure one of:
   - `WCVA_DATASET_PATH`
   - `WCVA_DATASET_URL`
   - `dataset_path` in Streamlit secrets
   - `dataset_url` in Streamlit secrets
   - local untracked fallback: `datasets/WCVA_W2_Anonymised_Dataset.csv`
2. **Local authority context** — optional override; by default the app uses `references/context/la_context_wales.csv`.
3. **`references/SROI_Wales_Voluntary_Sector/`** — SROI reference docs and the mind-map HTML (optional but needed for the SROI & References page).

The app includes an in-app **Deployment Health** page and a startup guard:

- If the private dataset is unavailable, the app falls back to the bundled sample fixture and enters explicit demo mode instead of failing deeper in the analysis flow.
- Optional reference assets are reported as missing in the health view but do not block general dashboard use.

By default, the Dockerfile **copies the whole project** into the image, but the private Wave 2 dataset is expected to be supplied outside Git. For self-hosting, use an environment variable or a read-only volume mount:

```yaml
services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - WCVA_DATASET_PATH=/app/runtime-data/WCVA_W2_Anonymised_Dataset.csv
    volumes:
      - ./runtime-data:/app/runtime-data:ro
      - ./references:/app/references:ro
```

Then ensure `./runtime-data/WCVA_W2_Anonymised_Dataset.csv` exists on the host before starting the stack. The checked-in local-authority context file under `references/context/` will continue to work unless you explicitly override it.

---

## Self-hosting on a server

### 1. Prepare the host

- Install Docker and Docker Compose (or Podman + podman-compose).
- Clone or copy the repo and data into a directory on the server.

### 2. Configure and run

```bash
cd /path/to/wcva_data_analysis
docker compose up -d
```

The app will listen on port **8501**. Use a reverse proxy (Nginx, Caddy, Traefik) in front of it for HTTPS and a friendly hostname.

### 3. Reverse proxy example (Nginx)

Example Nginx server block (adjust `your-domain` and paths):

```nginx
server {
    listen 80;
    server_name your-domain.example.org;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Then enable TLS (e.g. with Certbot) and reload Nginx.

### 4. Restart policy

The `docker-compose.yml` in this repo sets `restart: unless-stopped`, so the container starts again after a reboot. No extra process manager is required for basic self-hosting.

---

## Deploying to a cloud or PaaS

- **Streamlit Community Cloud**: use the GitHub repo, set **Main file** to `src/app.py`, and choose Python **3.11** or **3.12** in the app's **Advanced settings**. Community Cloud does not read a repo `runtime.txt` here. No Docker required there. Store the private dataset URL or runtime path in Secrets Manager; see `docs/HISTORY_REWRITE_AND_STREAMLIT_SECRETS.md`.
- **Generic cloud (AWS, GCP, Azure, etc.)**: build the image and run it on a container service (ECS, Cloud Run, ACI, etc.). Use the same environment variables and volume mounts as above; expose port 8501 and put a load balancer or API gateway in front if needed.
- **Kubernetes**: use the same image; define a Deployment and Service that expose 8501 and, if needed, mount datasets via a ConfigMap or PVC.

---

## Environment variables

| Variable | Description | Default |
|----------|-------------|--------|
| `WCVA_DEBUG_MEMORY` | Set to `1`, `true`, or `yes` to show process memory in the sidebar. | (off) |
| `WCVA_OUTPUT_DIR` | Override where generated presentation files are written. | `output/` under the project root |

Streamlit’s own settings (e.g. `STREAMLIT_SERVER_*`) are set in the Dockerfile so the app listens on `0.0.0.0:8501` inside the container. Override them only if you need a different port or address.

---

## Security and hardening

- The Dockerfile runs the app as a non-root user (`appuser`).
- Do not run the container as root in production.
- **Secrets**: Do not bake API keys, passwords, tokens, or private dataset URLs into the image. Use environment variables or mounted secret files (e.g. Streamlit Secrets) and keep `.env` or `secrets.toml` out of version control.
- If the dataset is sensitive, prefer **read-only volume mounts** or a secret-backed private URL and avoid baking it into the image.
- Use a reverse proxy for TLS and, if needed, authentication; the Streamlit app itself does not implement auth.

---

## Troubleshooting

- **App not loading**: ensure port 8501 is not in use and the container is running (`docker compose ps` or `docker ps`).
- **Missing data / empty dashboard**: confirm the app has a valid `WCVA_DATASET_PATH` or `WCVA_DATASET_URL` (or matching Streamlit secrets), and check the in-app Deployment Health page for the resolved source.
- **App is running in demo mode**: the private Wave dataset was not resolved, so the bundled sample fixture is being used. Configure a real dataset path/URL or mount the private data into the container.
- **Unsure which runtime file is missing**: open the in-app **Deployment Health** page after startup, or rely on the startup guard if the app stops immediately.
- **Permission errors**: if you use volume mounts, ensure the host directories are readable by the container user (UID 1000 in the Dockerfile).

For more on the app’s architecture and configuration, see `ARCHITECTURE.md` and `README.md`.
