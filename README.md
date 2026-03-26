<div align="center">

<h1>🚀 AI GTM Engine</h1>

<p><strong>Replace your entire Go-To-Market SaaS stack with one self-hosted AI platform.</strong></p>

<p>
  <a href="#quick-start"><img src="https://img.shields.io/badge/docker-compose%20up-blue?logo=docker" alt="Docker"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
  <a href="https://github.com/kalyaankummer/gtm-engine/actions"><img src="https://img.shields.io/github/actions/workflow/status/kalyaankummer/gtm-engine/ci.yml?label=CI" alt="CI"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"></a>
  <a href="#"><img src="https://img.shields.io/badge/next.js-14-black?logo=next.js" alt="Next.js 14"></a>
</p>

<p>
  <strong>6sense + Clay + Outreach + Gong → $0/month, runs on your own infra.</strong>
</p>

</div>

---

## What is this?

Most B2B companies pay **$80,000–$150,000/year** for a stack of GTM SaaS tools that don't talk to each other, lock your data behind APIs, and charge per seat. AI GTM Engine replaces them with **five autonomous AI agents** that run on your infrastructure, use your LLM API keys, and put you back in control.

```
6sense         → ICP Agent       (lead scoring + ideal customer profiling)
Clay           → Enrichment      (Apollo.io + Hunter.io pipeline)
Outreach       → Outbound Agent  (3 personalized email variations per lead)
Gong           → Deal Intel Agent (transcript analysis + deal risk scoring)
ChurnZero      → Retention Agent (health scoring + churn prediction)
```

**Everything is human-in-the-loop.** Agents draft, humans approve. No email ever sends without a click.

---

## ✨ Features

- **5 AI Agents** — ICP scoring, outbound personalization, content generation, deal intelligence, retention analysis
- **Human Approval Queue** — review AI drafts side-by-side before anything goes out
- **CRM Sync** — bidirectional HubSpot and Salesforce sync, every 4 hours
- **Data Enrichment** — Apollo.io + Hunter.io pipeline, auto-triggered on new leads
- **Any LLM** — OpenAI, Anthropic Claude, Ollama (local), or any LiteLLM-supported provider
- **Real-time Dashboard** — Next.js frontend with live agent status via SSE
- **Self-hostable** — one `docker-compose up` command, no cloud lock-in
- **Multi-tenant** — built-in org isolation, RBAC (admin / member / viewer)
- **Observability** — Prometheus metrics, Grafana dashboards, Langfuse LLM tracing
- **Open source** — MIT license, all data stays in your Postgres

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                     ┌─────▼─────┐
                     │   Nginx   │  rate limiting, SSL, static files
                     └─────┬─────┘
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼──────┐  ┌──────▼──────┐        │
    │  Next.js   │  │   FastAPI   │        │
    │  Frontend  │  │   Backend   │        │
    └────────────┘  └──────┬──────┘        │
                           │               │
              ┌────────────┼───────────┐   │
              │            │           │   │
        ┌─────▼────┐ ┌─────▼─────┐ ┌──▼───▼──┐
        │ Postgres │ │   Redis   │ │ Qdrant  │
        │+pgvector │ │  (cache + │ │(vector  │
        │          │ │  broker)  │ │ search) │
        └──────────┘ └─────┬─────┘ └─────────┘
                           │
                    ┌──────▼──────┐
                    │   Celery    │  async jobs, scheduled tasks
                    │  Workers    │
                    └─────────────┘
```

**Stack:** Python 3.11 · FastAPI · LangGraph · LiteLLM · SQLAlchemy 2.0 · Alembic · Celery · Next.js 14 · TypeScript · Tailwind · shadcn/ui · PostgreSQL 16 + pgvector · Redis 7 · Qdrant

---

## ⚡ Quick Start

**Prerequisites:** Docker 24+, Docker Compose 2.23+, and at least one LLM API key.

```bash
# 1. Clone
git clone https://github.com/kalyaankummer/gtm-engine.git
cd gtm-engine

# 2. Configure
cp .env.example .env
# Edit .env — set LLM_PROVIDER, LLM_API_KEY, JWT_SECRET, ENCRYPTION_KEY

# 3. Launch (everything: API, frontend, DB, Redis, Qdrant, workers)
docker compose up --build

# 4. Open the dashboard
open http://localhost:3000
```

**That's it.** The full stack is up in under 2 minutes.

> With observability (Prometheus + Grafana + Langfuse):
> ```bash
> docker compose --profile observability up --build
> ```

---

## 🤖 The Five Agents

### 1. ICP Agent — Lead Scoring
Trains on your best customers and scores every new lead against that profile using vector similarity + LLM reasoning. Returns a 0–1 score with fit signals and gap signals.

```python
# Train on your best customers
POST /agents/icp_agent/score  { "mode": "train", "profiles": [...] }

# Score a new lead
POST /agents/icp_agent/score  { "contact_profile": { "title": "VP Sales", ... } }
# → { "score": 0.87, "explanation": "...", "fit_signals": [...], "gap_signals": [...] }
```

### 2. Outbound Agent — Personalized Email
Generates 3 email variations per lead, each with a different personalization hook (recent news, job posting, tech stack change, pain point). Word-count enforced under 150. Never mentions AI.

```python
POST /agents/outbound_agent/generate
# → 3 variations go to approval queue, nothing sends without human approval
```

### 3. Deal Intelligence Agent — Risk Scoring
Analyzes CRM stage data, email threads, and call transcripts. Returns risk score, risk factors with evidence, and recommended actions with owner and urgency. Fires Slack alerts when risk > 0.75.

### 4. Retention Agent — Churn Prediction
Classifies accounts into 5 health states (Thriving → Critical), identifies the primary churn driver, and suggests the right playbook. Monitors contract renewal dates.

### 5. Content Agent — SEO Blog / Email Sequences / LinkedIn
Three modes: `SEO_BLOG_POST`, `EMAIL_SEQUENCE`, `LINKEDIN_POST`. Respects your brand voice config. Auto-flags quality issues: `too_salesy`, `missing_hook`, `over_length`, `weak_cta`.

---

## 🔌 Integrations

| Category | Supported |
|----------|-----------|
| LLM | OpenAI GPT-4o, Anthropic Claude, Ollama (local), any LiteLLM provider |
| CRM | HubSpot, Salesforce |
| Email | Gmail (OAuth), Outlook / Microsoft 365 |
| Enrichment | Apollo.io, Hunter.io |
| Notifications | Slack webhooks |

---

## 📊 Dashboard

The Next.js dashboard includes:

- **Pipeline view** — deal kanban with risk indicators
- **Leads list** — ICP score badges (green/amber/red), enrichment status
- **Approval queue** — side-by-side email variation review with edit + approve/reject
- **Analytics** — 4 tabs: Pipeline, Outbound, Retention, AI Usage & Cost
- **Agent cards** — status, last run, trigger button, run history
- **Settings** — LLM config, CRM connections, brand voice, team management

---

## ⚙️ Configuration

All configuration is via `.env`. See `.env.example` for every available option with documentation.

**Minimum required:**
```bash
# Auth
JWT_SECRET=<256-bit random string>
ENCRYPTION_KEY=<Fernet key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# At least one LLM provider
LLM_PROVIDER=openai          # or anthropic, ollama
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Database (auto-configured in Docker)
DATABASE_URL=postgresql+asyncpg://gtm:gtm_password@postgres:5432/gtm_engine
```

**Optional integrations** (all work without any of these — agents fall back gracefully):
```bash
HUBSPOT_ACCESS_TOKEN=...
APOLLO_API_KEY=...
HUNTER_API_KEY=...
GMAIL_OAUTH_TOKEN=...
SLACK_WEBHOOK_URL=...
```

---

## 🗄️ Database

Full PostgreSQL schema managed by Alembic:

```
organizations → users → contacts → email_sequences
                      → companies → deals
campaigns → email_sequences
agent_audit_log   (append-only, immutable)
agent_configurations
integrations
job_runs
```

Materialized views refreshed every 5 min: `mv_pipeline_summary`, `mv_outbound_performance`.

```bash
# Run migrations
make migrate
```

---

## 🧪 Testing

```bash
# All tests
make test

# Backend only
cd backend && pytest

# Frontend only
cd frontend && npm test
```

Tests use an in-process SQLite database — no running Postgres needed for unit tests. Integration tests spin up real Postgres and Redis via GitHub Actions services.

---

## 📁 Project Structure

```
gtm-engine/
├── backend/
│   ├── agents/          # 5 AI agents (ICP, Outbound, Content, Deal Intel, Retention)
│   ├── api/             # FastAPI routers + Pydantic schemas
│   ├── core/            # Auth, encryption, LLM router, rate limiting, circuit breaker
│   ├── db/              # SQLAlchemy models, repositories, Alembic migrations
│   ├── enrichment/      # Apollo + Hunter enrichment pipeline
│   ├── integrations/    # CRM, email, notification adapters
│   ├── prompts/         # Agent prompt templates (.txt files)
│   ├── services/        # Business logic layer
│   └── workers/         # Celery tasks + beat schedule
├── frontend/
│   ├── app/             # Next.js App Router pages
│   ├── components/      # React components (agents, leads, approvals, charts, ...)
│   └── lib/             # API client, Zustand store, TanStack Query hooks, types
├── infrastructure/
│   ├── nginx/           # Nginx config (rate limiting, SSE support, security headers)
│   ├── prometheus/      # Scrape config
│   └── grafana/         # Dashboards + datasource provisioning
├── docker-compose.yml   # Full stack (9 services)
├── Makefile             # Dev workflow shortcuts
└── .env.example         # Every config option documented
```

---

## 🔒 Security

- JWT access tokens (15 min) + refresh tokens (7 days, httpOnly cookie)
- AES-256-GCM field-level encryption for all stored credentials
- RBAC: admin / member / viewer roles with explicit permission sets
- Org-scoped multi-tenancy — every query is filtered by `org_id` from the JWT
- HMAC-SHA256 webhook verification
- Append-only audit log for all agent actions
- Rate limiting at Nginx (IP) and application (user/org) levels
- CORS strict origin whitelist

---

## 🗺️ Roadmap

- [ ] Pipedrive CRM integration
- [ ] LinkedIn outreach via Sales Navigator API
- [ ] Transcript ingestion from Zoom / Gong / Chorus
- [ ] Multi-step email sequences (automated follow-ups, still human-approved)
- [ ] A/B testing for email variations
- [ ] One-click deploy to Railway / Render / Fly.io
- [ ] Chrome extension for LinkedIn prospecting

---

## 🤝 Contributing

PRs are welcome. Please open an issue first for large changes.

```bash
# Setup dev environment
make setup
make dev

# Lint before submitting
make lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style and commit conventions.

---

## 📜 License

MIT — do whatever you want, including running it in production for your company.

---

<div align="center">

**Built by [Sai Sohan Merugu](https://github.com/kalyaankummer) · Artifex · Hyderabad**

*If this saves you money on your GTM stack, please ⭐ the repo — it helps more people find it.*

</div>
