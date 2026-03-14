# Docker and deployment guide

This document describes how to run the WCVA Baromedr Cymru Wave 2 Dashboard in Docker and how to self-host or deploy it on a server or cloud.

---

## Prerequisites

- **Docker** (Engine 20.10+) and **Docker Compose** (v2+), or a compatible container runtime (Podman, etc.).
- The **Wave 2 dataset** and any **reference assets** (see [Data and assets](#data-and-assets) below).

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

1. **`datasets/WCVA_W2_Anonymised_Dataset.csv`** — main Wave 2 survey data (required for the dashboard).
2. **`datasets/la_context_wales.csv`** — local authority context (required for profile/geography views).
3. **`references/SROI_Wales_Voluntary_Sector/`** — SROI reference docs and the mind-map HTML (optional but needed for the SROI & References page).

By default, the Dockerfile **copies the whole project** into the image, so any files present in `datasets/` and `references/` at build time are included. If you do **not** want to bake data into the image (e.g. for privacy or to swap datasets without rebuilding), use **volume mounts** with Compose:

```yaml
services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./datasets:/app/datasets:ro
      - ./references:/app/references:ro
```

Then ensure `datasets/` and `references/` on the host contain the required files before starting the stack.

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

- **Streamlit Community Cloud**: use the GitHub repo, set **Main file** to `src/app.py`, and choose Python **3.11** or **3.12** in the app's **Advanced settings**. Community Cloud does not read a repo `runtime.txt` here. No Docker required there.
- **Generic cloud (AWS, GCP, Azure, etc.)**: build the image and run it on a container service (ECS, Cloud Run, ACI, etc.). Use the same environment variables and volume mounts as above; expose port 8501 and put a load balancer or API gateway in front if needed.
- **Kubernetes**: use the same image; define a Deployment and Service that expose 8501 and, if needed, mount datasets via a ConfigMap or PVC.

---

## Environment variables

| Variable | Description | Default |
|----------|-------------|--------|
| `WCVA_DEBUG_MEMORY` | Set to `1`, `true`, or `yes` to show process memory in the sidebar. | (off) |

Streamlit’s own settings (e.g. `STREAMLIT_SERVER_*`) are set in the Dockerfile so the app listens on `0.0.0.0:8501` inside the container. Override them only if you need a different port or address.

---

## Security and hardening

- The Dockerfile runs the app as a non-root user (`appuser`).
- Do not run the container as root in production.
- **Secrets**: Do not bake API keys, passwords, or tokens into the image. Use environment variables or mounted secret files (e.g. Streamlit Secrets) and keep `.env` or `secrets.toml` out of version control.
- If the dataset or reference material is sensitive, prefer **read-only volume mounts** (as in the Compose example) and avoid baking secrets into the image.
- Use a reverse proxy for TLS and, if needed, authentication; the Streamlit app itself does not implement auth.

---

## Troubleshooting

- **App not loading**: ensure port 8501 is not in use and the container is running (`docker compose ps` or `docker ps`).
- **Missing data / empty dashboard**: confirm `datasets/WCVA_W2_Anonymised_Dataset.csv` (and, if used, `la_context_wales.csv`) exist in the image or in the mounted volume.
- **Permission errors**: if you use volume mounts, ensure the host directories are readable by the container user (UID 1000 in the Dockerfile).

For more on the app’s architecture and configuration, see `ARCHITECTURE.md` and `README.md`.
