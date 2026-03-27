# Configuration Reference

All configuration is via environment variables in `.env`. Copy `.env.example` to get started — every variable is commented inline.

---

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | Yes | `gtm_engine` | Database name |
| `POSTGRES_USER` | Yes | `gtm` | Database user |
| `POSTGRES_PASSWORD` | Yes | `gtm_password` | Database password — **change in production** |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://gtm:gtm_password@postgres:5432/gtm_engine` | Async SQLAlchemy URL used by the API and workers |
| `DATABASE_SYNC_URL` | Yes | `postgresql://gtm:gtm_password@postgres:5432/gtm_engine` | Sync URL used by Alembic migrations |
| `TEST_DATABASE_URL` | No | `postgresql+asyncpg://gtm:gtm_password@localhost:5433/gtm_engine_test` | Used by the integration test suite |

---

## Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | `redis://redis:6379/0` | Main cache and session store |
| `REDIS_PASSWORD` | No | _(empty)_ | Required for managed Redis (e.g. Redis Cloud, Upstash) |
| `REDIS_DB` | No | `0` | Redis database index for the app |
| `CELERY_BROKER_URL` | No | `redis://redis:6379/1` | Celery task queue broker |
| `CELERY_RESULT_BACKEND` | No | `redis://redis:6379/2` | Celery result storage |

---

## Qdrant (Vector Store)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_URL` | Yes | `http://qdrant:6333` | Qdrant base URL |
| `QDRANT_API_KEY` | No | _(empty)_ | Required for Qdrant Cloud |
| `QDRANT_COLLECTION_PREFIX` | No | `gtm_engine` | Namespace prefix for all collections |

---

## Authentication & Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | Yes | `change-me-in-production` | Signs JWT access tokens. Use `openssl rand -hex 32` to generate. |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL (stored in httpOnly cookie) |
| `CORS_ORIGINS` | Yes | `http://localhost:3000,http://localhost:8080` | Comma-separated list of allowed browser origins |
| `FRONTEND_ORIGIN` | Yes | `http://localhost` | Public frontend origin for cookie domain |
| `COOKIE_DOMAIN` | No | _(empty)_ | Set to your root domain in production (e.g. `.example.com`) |
| `ENCRYPTION_KEY` | Yes | `change-me-in-production` | Fernet key for field-level encryption of credentials. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `SECRET_BACKEND` | No | `env` | Secret storage backend: `env` or `vault` |
| `VAULT_ADDR` | No | _(empty)_ | HashiCorp Vault address (when `SECRET_BACKEND=vault`) |
| `VAULT_TOKEN` | No | _(empty)_ | Vault authentication token |

---

## LLM Providers

At least one provider API key is required for agents to function. The app falls back to heuristic scoring if no LLM is available.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | Yes | `openai` | Active LLM provider: `openai`, `anthropic`, `ollama` |
| `DEFAULT_LLM_MODEL` | Yes | `gpt-4.1-mini` | Model name for the default provider |
| `DEFAULT_EMBEDDING_MODEL` | Yes | `text-embedding-3-small` | Embedding model for vector search |
| `OPENAI_API_KEY` | No | _(empty)_ | OpenAI project API key |
| `ANTHROPIC_API_KEY` | No | _(empty)_ | Anthropic console API key |
| `OLLAMA_BASE_URL` | No | `http://ollama:11434` | Local Ollama service URL |

The LLM provider and model can also be changed at runtime from **Settings → LLM Config** in the UI. The `.env` values are the boot-time defaults.

---

## CRM Integrations

See [integrations.md](integrations.md) for OAuth setup instructions.

### HubSpot

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HUBSPOT_CLIENT_ID` | No | _(empty)_ | HubSpot developer app Client ID |
| `HUBSPOT_CLIENT_SECRET` | No | _(empty)_ | HubSpot developer app Client Secret |
| `HUBSPOT_REDIRECT_URI` | No | `http://localhost:8000/integrations/hubspot/callback` | OAuth callback URL — must match app config |

### Salesforce

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SALESFORCE_CLIENT_ID` | No | _(empty)_ | Salesforce Connected App Consumer Key |
| `SALESFORCE_CLIENT_SECRET` | No | _(empty)_ | Salesforce Connected App Consumer Secret |

---

## Email

See [integrations.md](integrations.md) for OAuth app setup.

### Gmail

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GMAIL_CLIENT_ID` | No | _(empty)_ | Google Cloud OAuth 2.0 Client ID |
| `GMAIL_CLIENT_SECRET` | No | _(empty)_ | Google Cloud OAuth 2.0 Client Secret |
| `GMAIL_REDIRECT_URI` | No | `http://localhost:8000/integrations/gmail/callback` | Authorized redirect URI |
| `EMAIL_FROM_ADDRESS` | No | `noreply@localhost` | Default sender address |

### Outlook / Microsoft 365

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OUTLOOK_CLIENT_ID` | No | _(empty)_ | Azure app registration Application (client) ID |
| `OUTLOOK_CLIENT_SECRET` | No | _(empty)_ | Azure app registration client secret value |
| `OUTLOOK_REDIRECT_URI` | No | `http://localhost:8000/integrations/outlook/callback` | Azure redirect URI |

---

## Data Enrichment

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APOLLO_API_KEY` | No | _(empty)_ | Apollo.io API key from account settings |
| `HUNTER_API_KEY` | No | _(empty)_ | Hunter.io API key from account settings |
| `ENABLE_LINKEDIN_SCRAPING` | No | `false` | Enable LinkedIn profile scraping (use with caution) |

---

## Notifications

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | No | _(empty)_ | Slack incoming webhook URL for deal risk alerts |
| `WEBHOOK_SECRET` | No | _(empty)_ | HMAC-SHA256 signing secret for outbound webhooks |

---

## Observability

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Python log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ENABLE_PROMETHEUS_METRICS` | No | `true` | Expose `/metrics` endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | _(empty)_ | OpenTelemetry collector endpoint for tracing |
| `PROMETHEUS_SCRAPE_INTERVAL_SECONDS` | No | `15` | Prometheus scrape interval |
| `GRAFANA_ADMIN_USER` | No | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | No | `admin` | Grafana admin password — **change in production** |
| `LANGFUSE_HOST` | No | `http://langfuse:3000` | Langfuse LLM tracing host |
| `LANGFUSE_PUBLIC_KEY` | No | _(empty)_ | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | No | _(empty)_ | Langfuse project secret key |
| `LANGFUSE_DATABASE_URL` | No | `postgresql://gtm:gtm_password@postgres:5432/langfuse` | Langfuse database connection |
| `LANGFUSE_REDIS_URL` | No | `redis://redis:6379/1` | Langfuse Redis connection |
| `LANGFUSE_NEXTAUTH_URL` | No | `http://localhost:3001` | Langfuse NextAuth base URL |
| `LANGFUSE_NEXTAUTH_SECRET` | No | `change-me-in-production` | Langfuse NextAuth secret — **change in production** |
| `LANGFUSE_SALT` | No | `change-me-in-production` | Langfuse password hashing salt — **change in production** |

---

## Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `http://localhost` | Browser-facing API origin (proxied through Nginx) |
| `NEXT_PUBLIC_APP_URL` | Yes | `http://localhost` | Browser-facing app base URL |
| `NEXT_PUBLIC_SSE_URL` | Yes | `http://localhost/events/agent-status` | Server-Sent Events stream URL for live agent status |
| `NEXT_TELEMETRY_DISABLED` | No | `1` | Set to `1` to disable Next.js telemetry |
| `API_INTERNAL_URL` | No | `http://api:8000` | Internal API URL for Next.js server-side proxying (Docker network) |

---

## Enterprise

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_ENTERPRISE` | No | `false` | Enable enterprise features |
| `ENTERPRISE_LICENSE_KEY` | No | _(empty)_ | License key (contact maintainers) |
| `OBJECT_STORAGE_ENDPOINT` | No | _(empty)_ | S3-compatible storage endpoint |
| `OBJECT_STORAGE_ACCESS_KEY_ID` | No | _(empty)_ | Storage access key |
| `OBJECT_STORAGE_SECRET_ACCESS_KEY` | No | _(empty)_ | Storage secret key |
| `OBJECT_STORAGE_BUCKET` | No | `gtm-engine` | Storage bucket name |
