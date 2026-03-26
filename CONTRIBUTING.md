# Contributing to AI GTM Engine

Thank you for helping make AI GTM Engine better. This document covers everything you need to get started.

## Ways to Contribute

- **Bug reports** — open an issue with steps to reproduce and your `.env` config (redact secrets)
- **Feature requests** — open an issue describing the use case, not just the feature
- **Code** — see the workflow below
- **Documentation** — fix typos, add examples, improve explanations
- **Integrations** — new CRM / email / enrichment providers are very welcome

## Development Setup

```bash
git clone https://github.com/kalyaankummer/gtm-engine.git
cd gtm-engine
cp .env.example .env
# Fill in JWT_SECRET, ENCRYPTION_KEY, and one LLM key
make setup
make dev
```

The full stack starts via Docker Compose. Hot-reload is enabled for both the FastAPI backend and Next.js frontend.

## Code Style

**Backend (Python)**
- Formatter: `ruff format` (via `make lint`)
- Linter: `ruff check` — zero warnings expected
- Type hints required on all public functions
- Async everywhere — no blocking I/O on the main thread

**Frontend (TypeScript)**
- Formatter: Prettier (via `npm run lint`)
- No `any` types without a comment explaining why
- TanStack Query for all server state — no raw `fetch` in components

## Adding a New Integration

All integrations implement a simple abstract interface:

```python
# CRM: backend/integrations/crm/base_crm.py
# Email: backend/integrations/email/base_email.py
# Enrichment: backend/integrations/data/base_enrichment.py
```

Create a new file, implement the interface, and add it to the integration factory in `backend/services/integration_service.py`. That's it.

## Adding a New Agent

1. Create `backend/agents/your_agent.py` extending `BaseAgent`
2. Add a prompt template to `backend/prompts/your_agent.txt`
3. Register it in `backend/api/routers/agents.py`
4. Write tests in `backend/tests/unit/test_your_agent.py`

## Pull Request Checklist

- [ ] `make lint` passes with zero warnings
- [ ] `make test` passes (all existing tests green)
- [ ] New code has tests
- [ ] No secrets or `.env` values committed
- [ ] PR description explains *why*, not just *what*

## Commit Messages

```
feat: add Pipedrive CRM integration
fix: handle Apollo 429 rate limit in enrichment pipeline
docs: add LinkedIn scraper setup guide
test: add unit tests for retention agent health scoring
```

## Reporting Security Issues

Do **not** open a public issue for security vulnerabilities. Email `kalyaankummer@gmail.com` directly.
