# Getting Started

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24+ | Includes Docker Compose v2 |
| Docker Compose | 2.23+ | Ships with Docker Desktop |
| Git | any | For cloning |
| LLM API key | — | OpenAI, Anthropic, or a local Ollama instance |

At least **4 GB of free RAM** is recommended. The full stack (including observability) needs 8 GB.

---

## 5-Step Setup

```bash
# Step 1 — Clone the repo
git clone https://github.com/sohan-a11y/gtm-engine.git
cd gtm-engine

# Step 2 — Copy the environment template
cp .env.example .env

# Step 3 — Fill in required secrets (open .env in your editor)
#   JWT_SECRET   → any 256-bit random string
#   ENCRYPTION_KEY → run: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#   OPENAI_API_KEY → or ANTHROPIC_API_KEY if you prefer Claude

# Step 4 — Start the full stack
docker compose up --build

# Step 5 — Open the dashboard
open http://localhost:3000
```

The full stack starts in under 2 minutes on a modern laptop. All services have health-check gates, so the API and frontend will not start until Postgres, Redis, and Qdrant are ready.

> **With observability (Prometheus + Grafana + Langfuse):**
> ```bash
> docker compose --profile observability up --build
> ```
> Grafana is at `http://localhost:3002`, Langfuse at `http://localhost:3001`.

---

## Minimum Required Variables

```bash
# Generate a JWT secret
openssl rand -hex 32

# Generate an encryption key (Fernet format)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set these in `.env`:

```ini
JWT_SECRET=<output from openssl rand -hex 32>
ENCRYPTION_KEY=<output from Fernet.generate_key>
OPENAI_API_KEY=sk-...          # or ANTHROPIC_API_KEY
```

Everything else has safe defaults for local development. See [configuration.md](configuration.md) for all variables.

---

## First-Run Checklist

After `docker compose up` succeeds and `http://localhost:3000` is reachable:

- [ ] **Create account** — click "Sign Up", enter name / email / password / org name
- [ ] **Complete onboarding wizard** — the wizard guides you through LLM provider selection and a quick brand voice setup
- [ ] **Connect a CRM** — go to Settings → Integrations → HubSpot or Salesforce and complete the OAuth flow (optional but recommended)
- [ ] **Import leads** — go to Leads → Import, upload a CSV with columns: `first_name`, `last_name`, `email`, `company_name`, `title`, `industry`
- [ ] **Run ICP scoring** — go to Agents → ICP Agent, click "Train" with a few sample profiles, then click "Score All Leads"

At this point the approval queue will start filling up with scored leads and generated email drafts ready for your review.

---

## Troubleshooting

### Postgres not ready / `connection refused` on startup

The API waits for Postgres to pass its health check before starting. If startup is slow:

```bash
# Check Postgres logs
docker compose logs postgres

# Manually verify health
docker compose exec postgres pg_isready -U gtm -d gtm_engine
```

If the volume is corrupted, reset it:
```bash
docker compose down -v   # WARNING: deletes all data
docker compose up --build
```

### Qdrant timeout on first request

Qdrant needs a few seconds to initialize its storage on first boot. The API uses a health-check gate (`/healthz`) with 5 retries and a 15-second interval. If you see Qdrant-related errors, wait 30 seconds and retry. If it persists:

```bash
docker compose logs qdrant
docker compose restart qdrant
```

### Next.js build error

If the frontend fails to build (common when pulling new commits), the build cache may be stale:

```bash
docker compose build --no-cache frontend
docker compose up frontend
```

If you see a TypeScript error, check that `NEXT_PUBLIC_API_BASE_URL` is set correctly in `.env`. It must match the URL your browser can reach (default: `http://localhost`).

### Port conflicts

Default ports used by the stack:

| Service | Port |
|---------|------|
| Nginx (main entry) | 80 |
| Frontend (Next.js) | 3000 |
| API (FastAPI) | 8000 |
| Postgres | 5432 |
| Redis | 6379 |
| Qdrant (HTTP) | 6333 |
| Qdrant (gRPC) | 6334 |
| Langfuse (observability) | 3001 |
| Grafana (observability) | 3002 |
| Prometheus (observability) | 9090 |

Change any port by adding `HOST_PORT:CONTAINER_PORT` overrides in `docker-compose.override.yml`.
