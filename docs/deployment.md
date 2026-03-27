# Deployment

## Docker Compose (Self-Hosted)

The `docker-compose.yml` in the repo root defines the complete stack. Run `docker compose up --build` to start all services.

### Services

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | Primary database with pgvector extension for embedding storage |
| `redis` | `redis:7-alpine` | 6379 | Cache, Celery broker, and session store. AOF persistence enabled, 256 MB memory cap with LRU eviction |
| `qdrant` | `qdrant/qdrant:latest` | 6333, 6334 | Vector search engine for ICP similarity lookups. HTTP on 6333, gRPC on 6334 |
| `api` | `./backend/Dockerfile` | 8000 | FastAPI application. Waits for postgres, redis, and qdrant health checks before starting |
| `worker` | `./backend/Dockerfile` | — | Celery worker for async agent jobs (enrichment, CRM sync, scoring) |
| `scheduler` | `./backend/Dockerfile` | — | Celery beat for scheduled tasks (CRM sync every 4h, deal risk scan every 6h, retention analysis every 12h) |
| `frontend` | `./frontend/Dockerfile` | 3000 | Next.js 14 dashboard. Depends on `api` being healthy |
| `nginx` | `nginx:1.25-alpine` | 80 | Reverse proxy. Routes `/api` and `/events` to the FastAPI service, everything else to Next.js. Handles rate limiting and security headers |

**Observability profile** (add `--profile observability`):

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `langfuse` | `langfuse/langfuse:latest` | 3001 | LLM call tracing and prompt versioning |
| `prometheus` | `prom/prometheus:v2.54.1` | 9090 | Metrics scraper. Config at `infrastructure/prometheus/prometheus.yml` |
| `grafana` | `grafana/grafana:11.1.0` | 3002 | Dashboards. Datasources and dashboards are provisioned automatically from `infrastructure/grafana/` |

---

## Environment Hardening Checklist

Before deploying to production, change these defaults:

- [ ] **`JWT_SECRET`** — generate with `openssl rand -hex 32`. The default `change-me-in-production` is insecure.
- [ ] **`ENCRYPTION_KEY`** — generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. All stored credentials are encrypted with this key — losing it means losing access to all stored integration tokens.
- [ ] **`POSTGRES_PASSWORD`** — change from `gtm_password` to a strong password.
- [ ] **`GRAFANA_ADMIN_PASSWORD`** — change from `admin`.
- [ ] **`LANGFUSE_NEXTAUTH_SECRET`** and **`LANGFUSE_SALT`** — change from `change-me-in-production`.
- [ ] **`CORS_ORIGINS`** — set to your production domain only (e.g. `https://gtm.yourcompany.com`).
- [ ] **`COOKIE_DOMAIN`** — set to your root domain (e.g. `.yourcompany.com`) so refresh token cookies scope correctly.
- [ ] **`FRONTEND_ORIGIN`** — set to your production frontend URL.
- [ ] **`NEXT_PUBLIC_API_BASE_URL`** and **`NEXT_PUBLIC_APP_URL`** — set to your production domain.
- [ ] Ensure ports 5432, 6379, 6333 are **not exposed** to the public internet — bind them to `127.0.0.1` or use a private network.

---

## Railway One-Click Deploy

A `railway.json` is included at the repo root. To deploy:

1. Push the repo to GitHub.
2. Go to [railway.app](https://railway.app), create a new project, and select **Deploy from GitHub repo**.
3. Add a PostgreSQL plugin and a Redis plugin to the project.
4. Set environment variables in the Railway dashboard (all variables from [configuration.md](configuration.md)).
5. Railway will build from `backend/Dockerfile` and start with the command in `railway.json`.

The health check path `/health` is used by Railway to determine when the deployment is healthy.

---

## Render Deploy

A `render.yaml` is included at the repo root. To deploy:

1. Push the repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Blueprint**.
3. Connect your GitHub repo. Render will read `render.yaml` and provision a web service, Postgres database, and Redis instance automatically.
4. Set any additional environment variables (LLM API keys, CRM credentials) in the Render dashboard under the service's **Environment** tab.

---

## Scaling

### Multiple Celery Workers

Run additional worker containers to increase agent throughput:

```bash
docker compose up --scale worker=4
```

Each worker picks up tasks from the Redis broker queue. Workers are stateless and can be scaled horizontally without coordination.

To dedicate a worker to a specific queue (e.g. only run enrichment tasks):

```bash
celery -A workers.celery_app:celery_app worker --queues=enrichment --loglevel=INFO
```

### Read Replicas

Point `DATABASE_URL` (used by the API for reads) to a read replica and keep `DATABASE_SYNC_URL` on the primary for Alembic migrations:

```ini
DATABASE_URL=postgresql+asyncpg://gtm:pass@replica.db:5432/gtm_engine
DATABASE_SYNC_URL=postgresql://gtm:pass@primary.db:5432/gtm_engine
```

---

## Backup

### PostgreSQL

```bash
# Dump to a compressed file
docker compose exec postgres pg_dump \
  -U gtm \
  -d gtm_engine \
  -F c \
  -f /tmp/gtm_engine_$(date +%Y%m%d).dump

# Copy out of the container
docker compose cp postgres:/tmp/gtm_engine_$(date +%Y%m%d).dump ./backups/

# Restore
docker compose exec postgres pg_restore \
  -U gtm \
  -d gtm_engine \
  /tmp/gtm_engine_backup.dump
```

Schedule this with cron or your cloud provider's managed backup feature.

### Redis

Redis is configured with AOF (append-only file) persistence in `docker-compose.yml`. The `redis_data` Docker volume persists data across restarts. For production, use a managed Redis with automatic backups (Redis Cloud, Upstash, AWS ElastiCache).

### Qdrant

Vector data is stored in the `qdrant_data` volume. Back it up by snapshotting the volume or using Qdrant's built-in snapshot API:

```bash
curl -X POST http://localhost:6333/collections/gtm_engine_icp_profiles/snapshots
```
