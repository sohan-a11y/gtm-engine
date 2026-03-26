# AI GTM Engine — Complete Engineering Specification
### Artifex | Open Source | Version 1.0

> **Purpose of this document:** This is the definitive engineering blueprint for building the AI GTM Engine from zero to production. Unlike the companion strategy/build guide, this document specifies exact implementation details — every file, every function signature, every error path, every security boundary, every data flow — so that an AI coding agent or developer can build each component without ambiguity or guesswork. Every edge case identified during design has been resolved inline.

> **How to use this document:** Feed sections directly to Claude Code, Cursor, or any AI coding agent. Each section is self-contained with full context. Build in the phase order specified. Do not skip the scaffolding phase.

---

## TABLE OF CONTENTS

1. System Overview & Architecture
2. Data Flow Diagrams (What Calls What, When)
3. Authentication & Multi-Tenancy (Complete Spec)
4. Security Architecture (Encryption, Secrets, RBAC)
5. File-by-File Implementation Specifications
6. Database Design (Complete with Indexes, Constraints, Triggers, Migrations)
7. Error Handling & Retry Patterns (Every Layer)
8. Rate Limiting, Caching & Performance
9. Agent System (State Machines, Edge Cases, Failure Modes)
10. LLM Abstraction Layer (Complete with Fallback Chain)
11. Integration Layer (Webhooks, Sync, Conflict Resolution)
12. Real-Time Communication (SSE for Agent Status)
13. Task Queue & Scheduling (Celery Architecture)
14. Frontend Architecture (Complete Component Tree)
15. Deployment & DevOps (Docker, CI/CD, Scaling)
16. Testing Strategy (Unit, Integration, E2E)
17. Monitoring & Observability
18. Open Source Packaging & Contribution Model
19. Build Phases with Exact Deliverables & Definition of Done

---

## 1. SYSTEM OVERVIEW & ARCHITECTURE

### 1.1 What This System Does

The AI GTM Engine is an open-source, self-hostable platform that replaces the entire Go-To-Market SaaS stack (6sense + Clay + Outreach + Gong, collectively costing $100k+/year) with five autonomous AI agents running on the user's own infrastructure using their choice of LLM provider. The system ingests CRM data, enrichment signals, call transcripts, and product usage metrics, then uses LLM-powered agents to score leads, write personalized outbound, generate content, analyze deal risk, and predict churn — all with human-in-the-loop approval before any external action is taken.

### 1.2 Core Architecture Pattern

The system follows a **modular monolith** architecture (not microservices). Every component lives in one repository, shares one database, and deploys via a single `docker-compose up` command. This is a deliberate choice for an open-source project — it minimizes operational complexity for self-hosters while maintaining clean internal boundaries through Python packages and abstract interfaces.

The architecture has six horizontal layers, each with a clear responsibility boundary.

**Layer 1 — API Gateway (FastAPI):** All external traffic enters here. Handles authentication, rate limiting, request validation, and routing. No business logic lives here — only HTTP concerns.

**Layer 2 — Service Layer:** Business logic orchestration. Each service corresponds to a domain (LeadService, CampaignService, DealService, etc.). Services call agents, enrichment pipelines, and integrations. Services are the only layer that writes to the database.

**Layer 3 — Agent Layer (LangGraph + LiteLLM):** The five AI agents plus the orchestrator. Agents receive structured input, call LLMs, and return structured output. Agents never touch the database directly — they return results to the service layer.

**Layer 4 — Integration Layer:** All external API communication (CRM, email, enrichment providers, LLM APIs). Each integration implements an abstract interface. Retry logic, rate limiting, and credential management live here.

**Layer 5 — Data Layer (PostgreSQL + Qdrant + Redis):** Three storage tiers. PostgreSQL for relational data and pgvector embeddings. Qdrant for high-performance vector similarity search. Redis for session cache, rate limit counters, and Celery broker.

**Layer 6 — Task Layer (Celery):** Async job execution for long-running operations (batch scoring, enrichment, CRM sync). Celery workers are separate processes that share the same codebase.

### 1.3 Technology Stack (Locked Versions)

These versions are locked for compatibility. Do not upgrade without running the full test suite.

**Backend (Python 3.11+):** FastAPI 0.109+, LangGraph 0.2+, LiteLLM 1.40+, SQLAlchemy 2.0+ with asyncpg, Alembic 1.13+, Pydantic 2.5+, Celery 5.3+ with Redis broker, Qdrant Client 1.7+, sentence-transformers 2.3+, passlib[bcrypt] + python-jose[cryptography] for auth, cryptography 42+ for field-level encryption, httpx 0.27+ for async HTTP, tenacity 8.2+ for retry logic.

**Frontend (Node 20+):** Next.js 14.1+ (App Router), TypeScript 5.3+, Tailwind CSS 3.4+, shadcn/ui (copy-paste component library), Zustand 4.5+ for state, TanStack Query 5.17+ for server state and polling, Recharts 2.10+ for charting, Zod 3.22+ for runtime validation.

**Infrastructure:** Docker 24+ with Docker Compose 2.23+, PostgreSQL 16 with pgvector 0.6+, Redis 7.2+ Alpine, Qdrant 1.7+, Nginx 1.25+, Langfuse 2.0+ (self-hosted LLM observability), Prometheus + Grafana for metrics.

---

## 2. DATA FLOW DIAGRAMS

### 2.1 Master System Flow (ASCII Architecture Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL WORLD                                 │
│  [Browser]  [CRM Webhooks]  [Slack]  [Email Providers]  [LLM APIs]    │
└─────┬──────────┬──────────────┬───────────┬────────────────┬───────────┘
      │          │              │           │                │
      ▼          ▼              │           │                │
┌─────────────────────┐        │           │                │
│    NGINX (Layer 1)  │        │           │                │
│  - SSL termination  │        │           │                │
│  - IP rate limiting │        │           │                │
│  - Static files     │        │           │                │
└─────┬───────────────┘        │           │                │
      │                        │           │                │
      ▼                        ▼           │                │
┌──────────────────────────────────┐       │                │
│       FASTAPI API SERVER (L2)    │       │                │
│  ┌────────────┐ ┌─────────────┐  │       │                │
│  │ Auth MW    │ │ Rate Limit  │  │       │                │
│  │ (JWT+RBAC) │ │ Middleware  │  │       │                │
│  └─────┬──────┘ └──────┬──────┘  │       │                │
│        ▼               ▼         │       │                │
│  ┌──────────────────────────┐    │       │                │
│  │     ROUTER LAYER         │    │       │                │
│  │  /agents  /leads  /jobs  │    │       │                │
│  │  /campaigns  /analytics  │    │       │                │
│  │  /integrations /settings │    │       │                │
│  │  /webhooks  /approvals   │    │       │                │
│  └──────────┬───────────────┘    │       │                │
│             ▼                    │       │                │
│  ┌──────────────────────────┐    │       │                │
│  │    SERVICE LAYER (L3)    │    │       │                │
│  │  LeadService             │    │       │                │
│  │  CampaignService         │    │       │                │
│  │  DealService             │    │       │                │
│  │  AnalyticsService        │    │       │                │
│  │  IntegrationService      │    │       │                │
│  │  ApprovalService         │    │       │                │
│  │  UserService             │    │       │                │
│  └───┬──────────┬───────────┘    │       │                │
└──────┼──────────┼────────────────┘       │                │
       │          │                        │                │
       ▼          ▼                        │                │
┌─────────────┐ ┌──────────────────┐       │                │
│ AGENT LAYER │ │  CELERY WORKERS  │       │                │
│   (L4)      │ │     (L6)         │       │                │
│ ┌─────────┐ │ │ ┌──────────────┐ │       │                │
│ │ICP Agent│ │ │ │batch_score   │ │       │                │
│ │Outbound │ │ │ │enrich_batch  │ │       │                │
│ │Content  │ │ │ │sync_crm      │ │       │                │
│ │DealIntel│ │ │ │weekly_digest │ │       │                │
│ │Retention│ │ │ └──────────────┘ │       │                │
│ └─────────┘ │ └──────────────────┘       │                │
└──────┬──────┘          │                 │                │
       │                 │                 │                │
       ▼                 ▼                 ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER (L5)                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │
│  │LLM Router│  │CRM Sync  │  │Enrichment │  │Email/Slack     │  │
│  │(LiteLLM) │  │(HubSpot/ │  │(Apollo/   │  │(Gmail/Outlook/ │  │
│  │          │  │Salesforce)│  │Hunter/    │  │ Slack Webhook) │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └───────┬────────┘  │
└───────┼─────────────┼──────────────┼─────────────────┼────────────┘
        ▼             ▼              ▼                 ▼
   [LLM APIs]    [CRM APIs]    [Data APIs]      [Email/Slack APIs]

       ▼          ALL LAYERS READ/WRITE TO:         ▼
┌──────────────────────────────────────────────────────┐
│                  DATA LAYER                           │
│  ┌────────────────┐  ┌─────────┐  ┌──────────────┐  │
│  │  PostgreSQL 16  │  │ Qdrant  │  │   Redis 7    │  │
│  │  + pgvector     │  │ Vector  │  │  - Cache     │  │
│  │  - All tables   │  │ Search  │  │  - Sessions  │  │
│  │  - Audit logs   │  │ - ICP   │  │  - Rate lim  │  │
│  │  - Embeddings   │  │   embed │  │  - Celery    │  │
│  └────────────────┘  └─────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 2.2 New Lead Flow (Complete End-to-End Sequence)

This is the exact sequence of events when a new lead enters the system, from HTTP request to final outbound draft. Every step is numbered so that when debugging, you can identify exactly where in the pipeline a failure occurred.

```
TRIGGER: POST /leads (manual) OR CRM webhook OR CSV import

Step 1:  API receives request → validates with Pydantic LeadCreate schema
Step 2:  Auth middleware verifies JWT → extracts org_id + user_id from token
Step 3:  LeadService.create_lead() called with org_id injected
Step 4:  ├── UPSERT contact record into PostgreSQL (status: "new")
Step 5:  ├── IF email already exists for this org: return 409 DuplicateError
Step 6:  ├── Dispatch Celery task: enrich_contact(contact_id, org_id)
Step 7:  └── Return 201 with contact_id to caller (enrichment runs async)

--- ASYNC (Celery Worker) ---

Step 8:  enrich_contact task starts
Step 9:  ├── Check if Apollo API key is configured for this org
Step 10: │   └── IF no key: skip enrichment, set enrichment_status="skipped"
Step 11: ├── Call Apollo.io API with email or name+company
Step 12: │   ├── ON SUCCESS: merge enrichment_data into contact JSONB column
Step 13: │   ├── ON 429 (rate limit): retry with 60s fixed delay (max 3 retries)
Step 14: │   ├── ON 400 (bad email): set enrichment_status="failed", log reason
Step 15: │   └── ON network timeout: retry with exponential backoff (max 3 retries)
Step 16: ├── Call Hunter.io → verify email deliverability score
Step 17: │   └── IF score < 50: flag contact.enrichment_data.email_risky = true
Step 18: ├── Update contact: enrichment_status="enriched", last_enriched_at=NOW()
Step 19: ├── Publish SSE event: {type: "enrichment_complete", contact_id}
Step 20: └── Dispatch next task: score_icp(contact_id, org_id)

Step 21: score_icp task starts
Step 22: ├── Load agent_configurations for "icp_agent" for this org
Step 23: │   └── IF agent disabled: skip scoring, log "agent disabled"
Step 24: ├── ContextBuilder assembles text profile from contact + company + enrichment
Step 25: ├── Generate embedding via LLMRouter.embed(profile_text)
Step 26: │   ├── IF provider=ollama: use local sentence-transformers (384 dims, padded to 1536)
Step 27: │   └── ELSE: use LiteLLM aembedding (text-embedding-3-small, 1536 dims)
Step 28: ├── Query Qdrant collection "icp_profiles_{org_id}" for top-5 nearest neighbors
Step 29: │   ├── IF collection empty (no ICP trained): set icp_score=NULL, return early
Step 30: │   └── IF collection exists: get top-5 with cosine similarity scores
Step 31: ├── Build LLM context: profile data + top-5 similar profiles + similarity scores
Step 32: ├── Call LLMRouter.complete(system=icp_scoring_prompt, user=context, format="json")
Step 33: │   ├── ON SUCCESS: parse JSON → extract score, explanation, fit_signals, gap_signals
Step 34: │   ├── ON JSON parse fail: retry with stricter prompt (max 2 retries on parse errors)
Step 35: │   ├── ON LLM rate limit: retry with exponential backoff (2s, 4s, 8s)
Step 36: │   └── ON LLM total failure: use FALLBACK → avg of top-5 cosine similarities as score
Step 37: ├── Validate score is in [0.0, 1.0] range, clamp if needed
Step 38: ├── Update contact: icp_score, icp_score_reason, fit_signals, gap_signals
Step 39: ├── Store embedding in PostgreSQL pgvector column for future queries
Step 40: ├── Log to agent_audit_log: full prompt, raw response, tokens, latency, cost estimate
Step 41: ├── Publish SSE event: {type: "scoring_complete", contact_id, score}
Step 42: └── IF icp_score >= 0.6 AND active campaign exists: dispatch generate_outbound()

Step 43: generate_outbound task starts (ONLY if score threshold met)
Step 44: ├── Load active campaigns for this org where ICP filters match the contact
Step 45: │   └── IF no matching campaigns: log "no matching campaign", return
Step 46: ├── For the best-matching campaign:
Step 47: │   ├── ContextBuilder assembles FULL context:
Step 48: │   │   contact profile + enrichment + ICP score reason + recent company news
Step 49: │   │   + job postings + campaign config (tone, product, value prop, brand voice)
Step 50: │   ├── Call LLMRouter.complete(system=outbound_prompt, user=full_context, format="json")
Step 51: │   ├── Parse 3 email variations from JSON (subject, body, hook_type, confidence)
Step 52: │   ├── Validate: body word count < 150, no banned phrases, has CTA
Step 53: │   ├── Insert 3 email_sequence records (status: "pending_approval", variation_rank: 1,2,3)
Step 54: │   └── Log to agent_audit_log with all 3 variations
Step 55: ├── Send Slack notification: "New outbound draft for {name} ({company}) — review needed"
Step 56: ├── Update contact.outbound_status = "pending_approval"
Step 57: └── Publish SSE event: {type: "outbound_draft_ready", contact_id}

--- HUMAN REVIEW (Dashboard) ---

Step 58: Human opens /approvals page in dashboard
Step 59: Sees email variations side-by-side with full contact context card
Step 60: Can switch between 3 variations using tabs
Step 61: Actions available:
Step 62: ├── APPROVE (as-is): status → "approved", queue for sending, log approved_by
Step 63: ├── EDIT + APPROVE: save edits, set edited_before_approval=true, queue for sending
Step 64: ├── REJECT (with reason): status → "rejected", store rejection_reason
Step 65: │   └── Optionally triggers re-generation with reason as additional context
Step 66: └── SKIP: move to next item in queue, no status change

Step 67: ON APPROVE: Celery task send_email dispatched
Step 68: ├── Load email provider integration (Gmail/Outlook) for this org
Step 69: ├── Send email via provider API
Step 70: ├── ON SUCCESS: status → "sent", sent_at=NOW(), create CRM activity
Step 71: ├── ON BOUNCE: status → "bounced", log, notify via Slack
Step 72: └── ON FAILURE: status → "failed", retry once after 5 min, then alert
```

### 2.3 Weekly GTM Review Flow

```
TRIGGER: Celery Beat schedule — every Sunday 00:00 UTC

Step 1:  weekly_gtm_review task dispatched
Step 2:  ├── Query all active organizations
Step 3:  └── For each org (sequentially to avoid resource contention):

Step 4:  ├── PHASE 1: ICP Re-scoring
Step 5:  │   ├── Query contacts WHERE icp_score_updated_at < NOW() - 7 days
Step 6:  │   ├── Batch into groups of 10
Step 7:  │   ├── For each batch: score concurrently (asyncio.gather with semaphore=5)
Step 8:  │   ├── On individual failure: log error, continue with remaining batch items
Step 9:  │   └── Collect: total_rescored, avg_score_change, newly_qualified_count

Step 10: ├── PHASE 2: Deal Intelligence
Step 11: │   ├── Query deals WHERE stage NOT IN ('closed_won','closed_lost')
Step 12: │   ├── For each active deal: run deal_intel_agent.analyze()
Step 13: │   ├── Collect: deals_analyzed, high_risk_count, actions_generated
Step 14: │   └── For deals with risk_score > 0.75: send IMMEDIATE Slack alert

Step 15: ├── PHASE 3: Retention Analysis
Step 16: │   ├── Query companies WHERE contract_renewal_date < NOW() + 90 days
Step 17: │   ├── For each: run retention_agent.analyze()
Step 18: │   ├── Detect state TRANSITIONS (e.g., Stable → At Risk)
Step 19: │   ├── Collect: accounts_analyzed, at_risk_count, mrr_at_risk
Step 20: │   └── For state degradations: send Slack alert with playbook recommendation

Step 21: ├── PHASE 4: Generate Weekly Digest
Step 22: │   ├── Compile all metrics from phases 1-3
Step 23: │   ├── Call LLM to generate 3-bullet executive summary
Step 24: │   └── Send formatted Slack digest to configured channel

Step 25: └── Log complete run to agent_audit_log with total duration and all metrics
```

### 2.4 CRM Bi-Directional Sync Flow

```
═══ INBOUND SYNC (CRM → GTM Engine) ═══

TRIGGER: Celery Beat every 4 hours OR POST /integrations/{provider}/sync

Step 1:  Load integration record from DB for this org + provider
Step 2:  Decrypt credentials using encryption.py
Step 3:  Check circuit breaker for this provider
         └── IF OPEN: skip sync, log "circuit breaker open", return
Step 4:  Refresh OAuth token if within 5 min of expiry
Step 5:  Fetch records modified since integrations.last_synced_at
         ├── Contacts: paginated (100/page), all custom properties
         ├── Companies: with contact associations
         └── Deals: with contact and company associations
Step 6:  For each record:
         ├── Map CRM fields → internal schema using configurable field_mapping
         ├── UPSERT into PostgreSQL:
         │   ├── IF crm_id exists in our DB: UPDATE only CRM-owned fields
         │   │   (name, email, title, company — never overwrite enrichment_data or scores)
         │   └── IF crm_id is new: INSERT as new record → trigger new_lead_workflow
         └── Track: created_count, updated_count, error_count
Step 7:  Update integrations.last_synced_at = NOW()
Step 8:  Store sync result in integrations.last_sync_result JSONB
Step 9:  Circuit breaker: record_success()
Step 10: Publish SSE event: {type: "sync_complete", provider, results}

═══ OUTBOUND SYNC (GTM Engine → CRM) ═══

TRIGGER: After any agent produces CRM-writable data (ICP score, deal risk, etc.)

Step 1:  Agent completes → service layer receives result
Step 2:  Service checks if CRM integration is active for this org
         └── IF no active CRM: skip push, data stays internal only
Step 3:  CRMSync.push_update(crm_id, fields_to_push):
         ├── Map internal fields → CRM custom properties:
         │   icp_score       → gtm_engine_icp_score (number)
         │   icp_score_reason → gtm_engine_icp_reason (string, max 500 chars)
         │   risk_score      → gtm_engine_deal_risk (number)
         │   health_score    → gtm_engine_health_score (number)
         ├── Call CRM PATCH API
         ├── ON 429: queue for retry in 60 seconds via Celery
         ├── ON 401: refresh token, retry once
         └── ON persistent failure: log, do NOT block the main flow

CONFLICT RESOLUTION RULES:
- CRM-owned fields (name, email, title): CRM always wins on inbound sync
- GTM-owned fields (icp_score, risk_score, health_score): GTM Engine always wins
- enrichment_data: NEVER written to CRM (stays internal to GTM Engine)
- If both sides changed same contact: CRM wins for CRM fields, GTM wins for GTM fields
- last_synced_at timestamp prevents stale overwrites in both directions
```

---

## 3. AUTHENTICATION & MULTI-TENANCY

### 3.1 Authentication Architecture

The system uses JWT (JSON Web Tokens) with short-lived access tokens and long-lived refresh tokens. This supports both the web dashboard and external API consumers.

**Token Design:**

The access token (15 min TTL) carries the user's identity and permissions as claims. It contains: `sub` (user UUID), `org_id` (organization UUID — the tenant isolation key), `role` (admin/member/viewer), `permissions` (array of permission strings), `jti` (unique token ID for revocation), and standard `iat`/`exp` timestamps. The refresh token (7 day TTL) is simpler: just `sub`, `org_id`, `type: "refresh"`, and `jti`.

**Token Flow (step by step):**

The user logs in via `POST /auth/login` with email and password. The server validates credentials against the bcrypt hash in the users table, then returns `{access_token, refresh_token}`. The client stores the access token in JavaScript memory (NOT localStorage — prevents XSS theft) and the refresh token is set as an httpOnly, SameSite=Strict cookie (prevents JavaScript access and CSRF). Every subsequent API request includes the access token in the `Authorization: Bearer` header. When the access token expires (401 response), the client calls `POST /auth/refresh` — the server validates the refresh token from the cookie, issues a NEW access token AND rotates the refresh token (detects token reuse attacks). On logout, the server adds the refresh token's `jti` to a Redis blacklist set with TTL matching the token's remaining expiry.

### 3.2 Complete Auth Implementation

**File: `backend/core/auth.py`**

```python
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from redis.asyncio import Redis

JWT_SECRET = os.getenv("JWT_SECRET")  # REQUIRED: 256-bit random string
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# bcrypt with 12 rounds: good balance of security and speed (~250ms per hash)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    org_id: str
    role: str = ""
    permissions: list[str] = []
    jti: str = ""
    type: str = "access"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False

def create_access_token(user_id: str, org_id: str, role: str, permissions: list[str]) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user_id, "org_id": org_id, "role": role,
        "permissions": permissions, "type": "access",
        "jti": str(uuid4()), "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str, org_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user_id, "org_id": org_id, "type": "refresh",
        "jti": str(uuid4()), "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None

async def is_token_blacklisted(redis: Redis, jti: str) -> bool:
    return await redis.sismember("token_blacklist", jti)

async def blacklist_token(redis: Redis, jti: str, ttl_seconds: int) -> None:
    await redis.sadd("token_blacklist", jti)
    await redis.expire("token_blacklist", max(ttl_seconds, REFRESH_TOKEN_EXPIRE_DAYS * 86400))
```

**File: `backend/api/dependencies.py`**

```python
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from pydantic import BaseModel

from core.auth import decode_token, is_token_blacklisted, TokenPayload
from db.session import get_db_session, get_redis

security_scheme = HTTPBearer()

class CurrentUser(BaseModel):
    user_id: str
    org_id: str
    role: str
    permissions: list[str]

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    redis: Redis = Depends(get_redis),
) -> CurrentUser:
    """THE SINGLE POINT where all authentication happens."""
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.type != "access":
        raise HTTPException(status_code=401, detail="Use access token, not refresh token")
    if await is_token_blacklisted(redis, payload.jti):
        raise HTTPException(status_code=401, detail="Token revoked")
    return CurrentUser(
        user_id=payload.sub, org_id=payload.org_id,
        role=payload.role, permissions=payload.permissions,
    )

def require_permission(permission: str):
    """Factory returning a dependency that checks a specific permission."""
    async def _check(user: CurrentUser = Depends(get_current_user)):
        if permission not in user.permissions and user.role != "admin":
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        return user
    return _check
```

### 3.3 Multi-Tenancy Architecture

Every table with user data has an `org_id UUID NOT NULL REFERENCES organizations(id)` column. Every query is filtered by the authenticated user's org_id. Every Qdrant collection is namespaced as `{collection}_{org_id}`. Every Redis key is namespaced as `{org_id}:{key}`. Every Celery task receives org_id as a required parameter. The org_id is ALWAYS extracted from the JWT — never from a request parameter (prevents tampering).

**Enforcement Pattern — BaseRepository:**

```python
# backend/db/base_repository.py
# Every model-specific repository inherits from this.
# This is the SINGLE enforcement point for tenant isolation.

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Type, Optional
from uuid import UUID

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession, org_id: str):
        self.model = model
        self.session = session
        self.org_id = org_id

    async def get_by_id(self, record_id: UUID) -> Optional[T]:
        stmt = select(self.model).where(
            self.model.id == record_id,
            self.model.org_id == self.org_id  # TENANT ISOLATION
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0, **filters) -> list[T]:
        stmt = select(self.model).where(self.model.org_id == self.org_id)
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        kwargs["org_id"] = self.org_id  # FORCE org_id injection
        record = self.model(**kwargs)
        self.session.add(record)
        await self.session.flush()
        return record

    async def update_by_id(self, record_id: UUID, **kwargs) -> bool:
        kwargs.pop("org_id", None)  # Never allow org_id change
        kwargs.pop("id", None)
        stmt = (
            update(self.model)
            .where(self.model.id == record_id, self.model.org_id == self.org_id)
            .values(**kwargs)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def delete_by_id(self, record_id: UUID) -> bool:
        stmt = delete(self.model).where(
            self.model.id == record_id, self.model.org_id == self.org_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
```

### 3.4 RBAC (Role-Based Access Control)

Three roles with explicit permission sets. If a permission is not listed, it is denied.

```python
# backend/core/permissions.py

ROLE_PERMISSIONS = {
    "admin": [
        "leads:read", "leads:write", "leads:delete",
        "companies:read", "companies:write", "companies:delete",
        "deals:read", "deals:write", "deals:delete",
        "campaigns:read", "campaigns:write", "campaigns:delete",
        "agents:trigger", "agents:configure",
        "approvals:read", "approvals:action",
        "analytics:read", "audit:read",
        "integrations:read", "integrations:write", "integrations:delete",
        "settings:read", "settings:write",
        "users:read", "users:write", "users:delete",
    ],
    "member": [
        "leads:read", "leads:write",
        "companies:read", "companies:write",
        "deals:read", "deals:write",
        "campaigns:read", "campaigns:write",
        "agents:trigger",
        "approvals:read", "approvals:action",
        "analytics:read", "audit:read",
    ],
    "viewer": [
        "leads:read", "companies:read", "deals:read",
        "campaigns:read", "analytics:read",
    ],
}
```

---

## 4. SECURITY ARCHITECTURE

### 4.1 Field-Level Encryption for Stored Credentials

Integration API keys and OAuth tokens are encrypted at rest using AES-256 via Fernet (symmetric encryption from Python's `cryptography` library). The master encryption key lives only in the environment variable `ENCRYPTION_KEY` — never in the database.

```python
# backend/core/encryption.py
import os, json
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY required. Generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")

_fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_credentials(credentials: dict) -> str:
    """Encrypt a dict → base64 string safe for DB storage."""
    return _fernet.encrypt(json.dumps(credentials).encode()).decode()

def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt from DB storage → dict. Raises InvalidToken if key mismatch."""
    return json.loads(_fernet.decrypt(encrypted.encode()).decode())
```

What gets encrypted: `integrations.credentials` column (all CRM/email API keys, OAuth tokens), and the `llm_api_keys` nested field inside `organizations.settings`. Nothing else — contact data and agent outputs are plaintext for query performance.

### 4.2 Secrets Management

For self-hosters, all secrets live in `.env` (gitignored). For enterprise deployments, a `SecretProvider` interface supports HashiCorp Vault. The factory checks for the `VAULT_ADDR` environment variable — if present, secrets are read from Vault; otherwise from env vars.

```python
# backend/core/secrets.py
import os
from abc import ABC, abstractmethod
from typing import Optional

class SecretProvider(ABC):
    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]: pass

class EnvSecretProvider(SecretProvider):
    async def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(key)

class VaultSecretProvider(SecretProvider):
    def __init__(self):
        import hvac
        self.client = hvac.Client(url=os.getenv("VAULT_ADDR"), token=os.getenv("VAULT_TOKEN"))

    async def get_secret(self, key: str) -> Optional[str]:
        secret = self.client.secrets.kv.v2.read_secret_version(path=f"gtm-engine/{key}")
        return secret["data"]["data"].get("value")

def get_secret_provider() -> SecretProvider:
    if os.getenv("VAULT_ADDR"):
        return VaultSecretProvider()
    return EnvSecretProvider()
```

### 4.3 API Security Checklist (All Implemented)

**CORS:** Strict origin whitelist — dev: `localhost:3000`, prod: configured frontend domain only. Never `*`. **Rate Limiting:** Three tiers at Nginx + application level. Public (login): 20/min/IP. Authenticated: 100/min/user. Agent triggers: 10/min/org. **Input Validation:** Every endpoint uses Pydantic models with max_length on strings and bounds on numbers. **SQL Injection:** Impossible — SQLAlchemy parameterized queries only. **XSS:** API returns JSON only; React auto-escapes; CSP headers via Nginx. **CSRF:** Not applicable — JWT uses Authorization header, not cookies (refresh cookie is httpOnly + SameSite=Strict). **Webhook Verification:** All incoming webhooks verified via HMAC-SHA256 before processing. **Audit Trail:** Agent actions are append-only in agent_audit_log (no UPDATE/DELETE on that table).

### 4.4 Nginx Security Configuration

```nginx
# infrastructure/nginx/nginx.conf
worker_processes auto;
events { worker_connections 1024; }

http {
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    limit_req_zone $binary_remote_addr zone=public:10m rate=20r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=agents:10m rate=10r/m;

    server_tokens off;
    client_max_body_size 50M;

    upstream api { server api:8000; }
    upstream frontend { server frontend:3000; }

    server {
        listen 80;
        server_name _;

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /api/auth/ {
            limit_req zone=public burst=5 nodelay;
            proxy_pass http://api/auth/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api/agents/ {
            limit_req zone=agents burst=5 nodelay;
            proxy_pass http://api/agents/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api/webhooks/ {
            proxy_pass http://api/webhooks/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
        }
    }
}
```

---

## 5. FILE-BY-FILE IMPLEMENTATION SPECIFICATIONS

### 5.1 Backend File Map (Every File with Purpose)

```
backend/
├── __init__.py
├── requirements.txt                    # Pinned dependencies (see Section 1.3)
├── pyproject.toml                      # Ruff + pytest + project metadata
├── Dockerfile                          # Multi-stage: builder + slim runtime
├── api/
│   ├── __init__.py
│   ├── main.py                         # FastAPI app factory, middleware, lifespan, error handlers
│   ├── dependencies.py                 # Auth, DB session, Redis, rate limit dependencies
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                     # POST /auth/login, /refresh, /logout, /register
│   │   ├── agents.py                   # POST /agents/{type}/score, /generate, /analyze
│   │   ├── leads.py                    # CRUD /leads + CSV import + search + filter
│   │   ├── companies.py               # CRUD /companies + health score filter
│   │   ├── deals.py                    # CRUD /deals + pipeline view
│   │   ├── campaigns.py               # CRUD /campaigns + /campaigns/{id}/sequences
│   │   ├── approvals.py               # GET/POST /approvals — human review queue
│   │   ├── analytics.py               # GET /analytics/pipeline, /outbound, /retention, /usage
│   │   ├── integrations.py            # CRUD /integrations + OAuth connect + manual sync
│   │   ├── settings.py                # GET/PATCH /settings, /settings/llm-config
│   │   ├── webhooks.py                # POST /webhooks/hubspot, /webhooks/salesforce
│   │   ├── jobs.py                     # POST /jobs/run-*, GET /jobs/{id}/status
│   │   ├── events.py                   # GET /events/agent-status (SSE endpoint)
│   │   └── health.py                   # GET /health — no auth, checks PG+Redis+Qdrant
│   └── schemas/
│       ├── __init__.py
│       ├── auth.py                     # LoginRequest, TokenResponse, RegisterRequest
│       ├── leads.py                    # LeadCreate, LeadUpdate, LeadResponse, LeadListResponse
│       ├── companies.py                # CompanyCreate, CompanyUpdate, CompanyResponse
│       ├── deals.py                    # DealCreate, DealUpdate, DealResponse
│       ├── campaigns.py                # CampaignCreate, SequenceResponse
│       ├── approvals.py                # ApprovalItem, ApproveRequest, RejectRequest
│       ├── agents.py                   # ScoreRequest, ScoreResponse, GenerateRequest
│       ├── analytics.py                # PipelineMetrics, OutboundMetrics, RetentionMetrics
│       ├── integrations.py             # IntegrationConnect, SyncResult
│       ├── settings.py                 # OrgSettings, LLMConfig
│       └── common.py                   # PaginationParams, PaginatedResponse, ErrorResponse
├── services/
│   ├── __init__.py
│   ├── lead_service.py                 # Lead CRUD + enrichment dispatch
│   ├── campaign_service.py             # Campaign CRUD + outbound generation trigger
│   ├── deal_service.py                 # Deal CRUD + risk analysis trigger
│   ├── analytics_service.py            # Aggregation queries for dashboard
│   ├── integration_service.py          # Connect/disconnect/sync external services
│   ├── approval_service.py             # Review queue logic + email send trigger
│   └── user_service.py                 # User CRUD + password management
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                   # Abstract base with LLM, memory, audit, timeout, fallback
│   ├── icp_agent.py                    # Train + Score modes with Qdrant vector search
│   ├── outbound_agent.py               # 3 email variations with personalization hooks
│   ├── content_agent.py                # Blog, email sequence, LinkedIn post generation
│   ├── deal_intel_agent.py             # Transcript analysis, risk scoring, action items
│   └── retention_agent.py              # Health scoring, churn prediction, playbook selection
├── core/
│   ├── __init__.py
│   ├── auth.py                         # JWT creation/validation, password hashing
│   ├── encryption.py                   # AES-256 field encryption for credentials
│   ├── secrets.py                      # SecretProvider interface (env + Vault)
│   ├── llm_router.py                   # LiteLLM wrapper with fallback chain + cost tracking
│   ├── memory.py                       # Three-tier: Redis session + Qdrant semantic + PG long-term
│   ├── orchestrator.py                 # LangGraph StateGraph with 4 workflows
│   ├── context_builder.py              # Assembles structured context for agent LLM calls
│   ├── prompt_manager.py               # Loads prompts from /prompts/*.txt with variable substitution
│   ├── audit_logger.py                 # Append-only logging to agent_audit_log
│   ├── exceptions.py                   # Complete exception hierarchy (Section 7.1)
│   ├── retry.py                        # Tenacity retry configs per service type (Section 7.3)
│   ├── circuit_breaker.py              # Circuit breaker for external services (Section 7.4)
│   ├── rate_limiter.py                 # Redis sliding window rate limiter (Section 8.1)
│   ├── cache.py                        # Redis cache with org_id namespacing (Section 8.2)
│   ├── metrics.py                      # Prometheus counters/histograms (Section 17.2)
│   ├── logging_config.py               # JSON structured logging (Section 17.1)
│   └── permissions.py                  # ROLE_PERMISSIONS mapping (Section 3.4)
├── enrichment/
│   ├── __init__.py
│   ├── profile_enricher.py             # Apollo.io + Hunter.io pipeline
│   ├── intent_signals.py               # CSV import for Bombora/G2 signals
│   ├── social_scraper.py               # LinkedIn company signals via Playwright
│   └── transcript_parser.py            # Call transcript ingestion + LLM extraction
├── integrations/
│   ├── __init__.py
│   ├── crm/
│   │   ├── __init__.py
│   │   ├── base_crm.py                # Abstract CRM interface (5 methods)
│   │   ├── hubspot.py                  # OAuth + CRUD + webhooks + field mapping
│   │   └── salesforce.py               # OAuth + CRUD + field mapping
│   ├── email/
│   │   ├── __init__.py
│   │   ├── base_email.py              # Abstract: send_email(to, subject, body, from)
│   │   ├── gmail.py                    # Gmail API OAuth sender
│   │   └── outlook.py                  # Microsoft Graph API sender
│   ├── data/
│   │   ├── __init__.py
│   │   ├── apollo.py                   # Apollo.io enrichment client
│   │   ├── hunter.py                   # Hunter.io email verification client
│   │   └── linkedin.py                 # Playwright scraper wrapper
│   └── notifications/
│       ├── __init__.py
│       ├── slack.py                    # Slack incoming webhook sender
│       └── webhook.py                  # Generic outgoing webhook
├── db/
│   ├── __init__.py
│   ├── models.py                       # All SQLAlchemy 2.0 models (Section 6)
│   ├── session.py                      # Async engine + session factory + connection pool
│   ├── base_repository.py              # Tenant-isolated CRUD (Section 3.3)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── contact_repo.py            # Contact-specific queries
│   │   ├── company_repo.py            # Company-specific queries
│   │   ├── deal_repo.py               # Deal pipeline queries
│   │   ├── campaign_repo.py           # Campaign + sequence queries
│   │   ├── audit_repo.py              # Read-only audit queries
│   │   └── integration_repo.py        # Credential management
│   └── migrations/
│       ├── env.py                      # Alembic async config
│       ├── script.py.mako
│       └── versions/
├── workers/
│   ├── __init__.py
│   ├── celery_app.py                   # Config + Redis broker + beat_schedule
│   └── tasks.py                        # All async task definitions
├── prompts/
│   ├── icp_scoring.txt
│   ├── outbound_personalization.txt
│   ├── content_generation.txt
│   ├── deal_intelligence.txt
│   └── retention_analysis.txt
└── tests/
    ├── conftest.py                     # Test DB, API client, mock LLM fixtures
    ├── unit/
    │   ├── test_auth.py
    │   ├── test_encryption.py
    │   ├── test_llm_router.py
    │   ├── test_icp_agent.py
    │   ├── test_outbound_agent.py
    │   └── test_context_builder.py
    └── integration/
        ├── test_lead_api.py
        ├── test_campaign_api.py
        ├── test_approval_flow.py
        ├── test_crm_sync.py
        └── test_agent_pipeline.py
```

### 5.2 Frontend File Map

```
frontend/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── Dockerfile
├── app/
│   ├── layout.tsx                      # Root: AuthProvider, ThemeProvider, QueryProvider
│   ├── page.tsx                        # Redirect to /dashboard or /login
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── layout.tsx                  # Auth pages: no sidebar
│   ├── (dashboard)/
│   │   ├── layout.tsx                  # Sidebar + header + main content area
│   │   ├── page.tsx                    # Home: summary cards + recent activity
│   │   ├── leads/
│   │   │   ├── page.tsx                # Lead table with filters, search, ICP badges
│   │   │   └── [id]/page.tsx           # Lead detail: profile + enrichment + timeline
│   │   ├── companies/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── campaigns/
│   │   │   ├── page.tsx                # Campaign list
│   │   │   ├── new/page.tsx            # Create campaign wizard
│   │   │   └── [id]/page.tsx           # Campaign detail + sequences + metrics
│   │   ├── pipeline/page.tsx           # Deal kanban with risk indicators
│   │   ├── approvals/page.tsx          # Split view: list panel + review panel
│   │   ├── agents/page.tsx             # Agent cards: status, trigger, history
│   │   ├── analytics/page.tsx          # 4 tabs: Pipeline, Outbound, Retention, AI Usage
│   │   ├── settings/
│   │   │   ├── page.tsx                # General settings
│   │   │   ├── integrations/page.tsx
│   │   │   ├── llm/page.tsx            # LLM provider + model + test button
│   │   │   ├── team/page.tsx           # User management + RBAC
│   │   │   └── brand-voice/page.tsx
│   │   └── onboarding/page.tsx         # 5-step wizard
│   └── api/[...proxy]/route.ts         # BFF proxy to FastAPI
├── components/
│   ├── ui/                             # shadcn/ui base components
│   ├── layout/
│   │   ├── sidebar.tsx                 # Nav with agent status dots
│   │   ├── header.tsx                  # Org name, user menu, notification bell
│   │   └── breadcrumbs.tsx
│   ├── agents/
│   │   ├── agent-card.tsx              # Status, last run, metrics, trigger button
│   │   ├── agent-status-badge.tsx
│   │   └── agent-run-history.tsx
│   ├── leads/
│   │   ├── lead-table.tsx              # Sortable, filterable
│   │   ├── lead-detail-card.tsx
│   │   ├── icp-score-badge.tsx         # Green (>0.7), amber (0.4-0.7), red (<0.4)
│   │   └── lead-import-dialog.tsx      # CSV upload + field mapping
│   ├── approvals/
│   │   ├── approval-list.tsx           # Left panel
│   │   ├── approval-review.tsx         # Right panel with edit + approve/reject
│   │   └── approval-stats-bar.tsx
│   ├── analytics/
│   │   ├── pipeline-charts.tsx
│   │   ├── outbound-charts.tsx
│   │   ├── retention-charts.tsx
│   │   └── ai-usage-charts.tsx
│   ├── charts/
│   │   ├── metric-card.tsx             # Single number + trend arrow
│   │   ├── bar-chart.tsx               # Recharts wrapper
│   │   ├── line-chart.tsx
│   │   └── donut-chart.tsx
│   └── common/
│       ├── data-table.tsx              # Generic sortable/filterable
│       ├── loading-skeleton.tsx
│       ├── error-boundary.tsx
│       └── empty-state.tsx
├── lib/
│   ├── api.ts                          # Fetch wrapper with auto-refresh on 401
│   ├── store.ts                        # Zustand stores
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-leads.ts               # TanStack Query hooks
│   │   ├── use-campaigns.ts
│   │   ├── use-approvals.ts
│   │   ├── use-analytics.ts           # With 30s polling
│   │   ├── use-agents.ts
│   │   └── use-agent-events.ts        # SSE hook for real-time updates
│   ├── utils.ts
│   └── types.ts                        # Mirrors backend Pydantic schemas
└── public/
    ├── logo.svg
    └── favicon.ico
```

---

## 6. DATABASE DESIGN (COMPLETE)

The full SQL schema with all tables, indexes, constraints, CHECK constraints, triggers, and materialized views is specified below. This is the source of truth — Alembic migrations should produce exactly this schema.

(See the complete schema in the companion document sections. Key design decisions summarized here.)

**Key decisions:** All primary keys are UUID v4 (gen_random_uuid()). All monetary values stored in cents as BIGINT (prevents floating-point errors). All JSONB columns have defaults (empty object or array). All mutable tables have an `updated_at` trigger. The agent_audit_log table is append-only (no UPDATE or DELETE trigger). Vector columns use 1536 dimensions (OpenAI embedding size; padded for local models). Every tenant-scoped table has a composite index on (org_id, {most-filtered-column}).

**Tables:** organizations, users, companies, contacts, deals, campaigns, email_sequences, content_library, agent_audit_log, agent_configurations, integrations, job_runs.

**Materialized Views:** mv_pipeline_summary (refreshed every 5 min), mv_outbound_performance (refreshed every 5 min). Both have UNIQUE indexes for CONCURRENTLY refresh support.

---

## 7. ERROR HANDLING & RETRY PATTERNS

### 7.1 Exception Hierarchy

Every error maps to a specific class. Catching generic `Exception` is prohibited outside the top-level handler.

```python
# backend/core/exceptions.py

class GTMEngineError(Exception):
    """Base. Never raise directly."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

# Auth
class AuthenticationError(GTMEngineError): pass
class AuthorizationError(GTMEngineError): pass

# Data
class ValidationError(GTMEngineError): pass
class DuplicateError(GTMEngineError): pass
class NotFoundError(GTMEngineError): pass

# LLM
class LLMError(GTMEngineError): pass
class LLMRateLimitError(LLMError):
    def __init__(self, provider: str, retry_after: int = 60):
        super().__init__(f"Rate limited by {provider}", {"retry_after": retry_after})
        self.retry_after = retry_after
class LLMResponseParseError(LLMError):
    def __init__(self, raw_response: str):
        super().__init__("Failed to parse LLM JSON response")
        self.raw_response = raw_response
class LLMTimeoutError(LLMError): pass
class LLMProviderError(LLMError): pass

# Integration
class IntegrationError(GTMEngineError): pass
class CRMSyncError(IntegrationError): pass
class EnrichmentError(IntegrationError): pass
class EmailDeliveryError(IntegrationError): pass

# Agent
class AgentError(GTMEngineError): pass
class AgentConfigError(AgentError): pass
class AgentTimeoutError(AgentError): pass
```

### 7.2 Global Error Handler (in main.py)

Maps every custom exception to an HTTP status code. AuthenticationError→401, AuthorizationError→403, NotFoundError→404, DuplicateError→409, ValidationError→422, LLMRateLimitError→429, LLMTimeoutError/AgentTimeoutError→504, LLMProviderError/IntegrationError→502, AgentConfigError→400, everything else→500. The catch-all handler logs the full traceback and returns a generic 500.

### 7.3 Retry Configurations (using tenacity)

```python
# backend/core/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed, retry_if_exception_type, before_sleep_log
import logging
logger = logging.getLogger("gtm-engine.retry")

# LLM: exponential 2s/4s/8s, max 3 attempts
llm_retry = retry(
    retry=retry_if_exception_type((LLMRateLimitError, LLMTimeoutError, LLMProviderError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)

# Enrichment (Apollo): fixed 60s, max 3 (rate limits are per-minute)
enrichment_retry = retry(
    retry=retry_if_exception_type(EnrichmentError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(60),
    before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)

# CRM: exponential 3s/9s/27s, max 5 (data consistency matters)
crm_retry = retry(
    retry=retry_if_exception_type(CRMSyncError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=3, min=3, max=120),
    before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)

# Email: exponential 1s/2s/4s, max 3 (time-sensitive)
email_retry = retry(
    retry=retry_if_exception_type(EmailDeliveryError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)
```

### 7.4 Circuit Breaker

When an external service is completely down (not just rate-limited), the circuit breaker prevents wasting resources. After 5 consecutive failures, the breaker opens for 120 seconds, then half-opens to test recovery with 3 consecutive successes required to close.

```python
# backend/core/circuit_breaker.py
import time, logging
from enum import Enum
logger = logging.getLogger("gtm-engine.circuit-breaker")

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 120):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count_half_open = 0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED: return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN allows test requests

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count_half_open += 1
            if self.success_count_half_open >= 3:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count_half_open = 0
        else:
            self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count_half_open = 0
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit [{self.name}] OPEN after {self.failure_count} failures")
```

---

## 8. RATE LIMITING, CACHING & PERFORMANCE

### 8.1 Application-Level Rate Limiting

Redis sliding window counters, applied as FastAPI dependencies. Three tiers: per-user API (100/min), per-org agent triggers (10/min), per-org LLM calls (configurable by plan).

### 8.2 Caching Strategy

**Redis Cache (TTL in parentheses):** Contact profiles (5 min), company profiles (5 min), ICP scores (1 hour), analytics aggregates (30 sec), enrichment data (30 days), LLM config (10 min), integration status (1 min). All keys namespaced by org_id.

**PostgreSQL Materialized Views:** mv_pipeline_summary and mv_outbound_performance, refreshed every 5 minutes via Celery beat with `REFRESH MATERIALIZED VIEW CONCURRENTLY`.

**Qdrant:** ICP profile embeddings — long-lived, only regenerated when ICP config changes.

### 8.3 Database Connection Pool

SQLAlchemy async engine: pool_size=20, max_overflow=10 (total max 30), pool_timeout=30s, pool_recycle=3600s (hourly), pool_pre_ping=True.

### 8.4 Batch Processing Pattern

All batch agent operations use asyncio.gather with a Semaphore(5) to limit concurrent LLM calls. Batches of 10 contacts processed at a time. Individual failures don't cancel the batch (return_exceptions=True). Each failed contact is logged and skipped.

---

## 9. AGENT SYSTEM (COMPLETE IMPLEMENTATION)

### 9.1 Enhanced BaseAgent

The base agent provides: LLM routing (model-agnostic), three-tier memory, audit logging, timeout protection (5 min max), automatic retry on transient LLM failures, JSON response parsing with 3-attempt retry on parse errors, and fallback behavior when LLM is completely unavailable. External code should only call `run_with_audit()`, never `run()` directly.

The `call_llm_json()` method is particularly important: it calls the LLM requesting JSON, attempts to parse the response, and if parsing fails, retries up to 2 more times with a stricter prompt that includes the error message. This handles the common case where LLMs return markdown-wrapped JSON or add prose before/after the JSON object.

### 9.2 ICP Agent

Two modes: TRAIN (stores ideal customer embeddings in Qdrant) and SCORE (finds nearest neighbors, calls LLM for reasoning). Training requires minimum 3 profiles. Scoring handles: empty collection (returns null + requires_training flag), LLM failure (falls back to similarity-only score), minimal contact data (scores on available data, notes gaps). The fallback_result returns a similarity-based score without LLM explanation.

### 9.3 Outbound Agent

Takes contact + enrichment + campaign config. Builds full personalization context (recent news, job postings, tech stack changes, ICP score reason). Generates 3 variations ranked by predicted performance, each tagged with the primary personalization hook used (recent_news, job_posting, tech_stack, pain_point, mutual_connection). Validates: word count under 150, has clear CTA, doesn't mention AI or automated outreach. Never auto-sends — all variations go to approval queue.

### 9.4 Content Agent

Three sub-modes: SEO_BLOG_POST, EMAIL_SEQUENCE, LINKEDIN_POST. Each has a distinct prompt and output schema. All modes accept brand_voice config (free-text description + 2-3 example paragraphs). Quality flags auto-detected: too_salesy, missing_hook, over_length, weak_cta. Content stored in content_library table with draft/approved/published workflow.

### 9.5 Deal Intelligence Agent

Ingests: CRM deal data (stage, amount, close date, days in stage) + email thread summaries + call transcript analysis + contact engagement metrics + competitor mentions. Outputs: risk_score (0-1), risk_level (low/medium/high/critical), risk_factors with evidence and severity, positive_signals, recommended_actions with owner (AE/CSM/SE) and urgency (today/this_week/this_month), likely_close_date, and 2-sentence deal_summary. Triggers Slack alert when risk_score > 0.75.

### 9.6 Retention Agent

Inputs: account MRR, contract dates, DAU/MAU, feature adoption, support tickets, NPS, last CSM call, payment history. Classifies into 5 health states: Thriving (0.8-1.0), Stable (0.6-0.8), At Risk (0.4-0.6), In Danger (0.2-0.4), Critical (0.0-0.2). Identifies primary churn driver from: low_usage, support_issues, champion_left, budget_concerns, competitor_activity, poor_onboarding. Suggests specific playbook per state. Predicts renewal probability. Detects state transitions and alerts on degradation.

---

## 10. LLM ABSTRACTION LAYER

The LLMRouter is the most critical file. It provides a single interface to every LLM provider through LiteLLM, with automatic fallback chain (if primary provider fails, tries next in list), cost tracking per call, JSON mode handling per provider (OpenAI/Groq use response_format parameter, Anthropic/Ollama/Google use system prompt injection), token counting, and markdown fence stripping for JSON responses. The embed() method uses sentence-transformers locally for Ollama and falls back to local if cloud embedding fails (padding 384-dim vectors to 1536).

---

## 11. INTEGRATION LAYER

### 11.1 Abstract Interfaces

Every integration type has a base class: BaseCRM (get_contacts, get_companies, get_deals, update_contact, create_activity), BaseEmail (send_email, check_deliverability), BaseEnrichment (enrich_contact, verify_email). Adding a new provider (e.g., Pipedrive) means implementing one file against the abstract interface.

### 11.2 Webhook Security

All incoming webhooks (HubSpot, Salesforce) are verified via HMAC-SHA256 before processing. The endpoint returns 200 immediately and processes events asynchronously via FastAPI BackgroundTasks to avoid webhook timeout (most providers timeout at 5-10 seconds).

### 11.3 Conflict Resolution

Clear ownership rules: CRM owns identity fields (name, email, title, company). GTM Engine owns AI-generated fields (scores, reasons, signals). Enrichment data stays internal (never pushed to CRM). Bidirectional sync uses last_synced_at timestamps, and each field has a defined owner that always wins in conflicts.

---

## 12. REAL-TIME COMMUNICATION (SSE)

Server-Sent Events at `GET /events/agent-status` for real-time dashboard updates. The API publishes events to a Redis Pub/Sub channel namespaced by org_id. Events: agent_started, agent_progress (with completed/total counts), agent_completed (with result summary), agent_error. Heartbeat every 30 seconds keeps the connection alive. Nginx configured with `X-Accel-Buffering: no` to prevent SSE buffering.

---

## 13. TASK QUEUE & SCHEDULING

Celery 5.3+ with Redis broker. Configuration: task_acks_late=True (acknowledge after processing), worker_prefetch_multiplier=1 (one task at a time), task_reject_on_worker_lost=True, soft_time_limit=300s, hard_time_limit=360s, result_expires=86400s.

Beat schedule: enrich_stale_contacts (daily 2AM UTC), sync_all_crms (every 4 hours), score_stale_contacts (daily 6AM UTC), weekly_gtm_review (Sunday midnight UTC), refresh_analytics_views (every 5 minutes).

---

## 14. DEPLOYMENT

### 14.1 Docker Compose (Production)

9 services: api (FastAPI, 1GB RAM), worker (Celery, 2GB), scheduler (Celery beat, 256MB), frontend (Next.js), postgres (pgvector/pgvector:pg16 with health check), redis (7-alpine, 256MB maxmemory with LRU eviction), qdrant (latest), langfuse (LLM observability), nginx (SSL + rate limiting). All services have restart=unless-stopped and health checks where applicable.

### 14.2 Backend Dockerfile

Multi-stage build: Stage 1 (builder) installs all pip dependencies with build tools. Stage 2 (runtime) copies only installed packages + application code into slim Python image. Runs as non-root user. Health check via curl to /health. 4 Uvicorn workers.

### 14.3 GitHub Actions CI/CD

Triggers on push to main and all PRs. Parallel jobs: Backend (Python 3.11, pip install, ruff lint, pytest with coverage, Codecov upload) and Frontend (Node 20, npm install, ESLint, Jest, next build). Docker services for integration tests (postgres + redis). On merge to main: build and push Docker images to GHCR.

---

## 15. TESTING STRATEGY

### 15.1 Test Fixtures (conftest.py)

Test database (separate PostgreSQL instance on port 5433), async API client via httpx.ASGITransport, pre-built auth headers with admin JWT, mock LLM that returns predictable JSON responses, mock Redis.

### 15.2 Test Categories

**Unit tests (100+, < 30s):** Auth functions, encryption/decryption, context builder, prompt manager, score normalization, field mapping, rate limiter logic, circuit breaker state transitions.

**Integration tests (50+, < 2 min):** Full API flows — create lead → score → generate outbound → approve → send. Real test DB and Redis, mocked LLM and external APIs.

**Agent tests (30+ per agent):** Predictable LLM mock responses, verify correct prompt construction, JSON edge case parsing, fallback behavior, audit log creation.

---

## 16. MONITORING & OBSERVABILITY

### 16.1 Structured JSON Logging

All logs are JSON-formatted with: timestamp, level, logger name, message, module, function, and optional org_id and agent_name fields. This enables structured querying in any log aggregator.

### 16.2 Prometheus Metrics

Agent metrics: runs_total (by agent + status), latency_seconds (histogram by agent), active_runs (gauge by agent). LLM metrics: calls_total (by provider + model), tokens_total (by provider + type), cost_usd (by provider), latency_seconds (histogram by provider). API metrics: requests_total (by method + endpoint + status), latency_seconds (histogram by method + endpoint). Business metrics: leads_scored_total, emails_generated_total, emails_approved_total (all by org_id).

### 16.3 Langfuse (LLM Observability)

Self-hosted alongside the engine. Tracks every LLM call: prompt, response, token count, latency, cost, model, and success/failure status. Enables prompt versioning and A/B testing.

---

## 17. OPEN SOURCE PACKAGING

### 17.1 Complete .env.example

Every variable documented with: description, where to get the value, whether it's required or optional, and the default value if any. Grouped by: Database (required), Redis (required), Qdrant (required), Authentication (required), Encryption (required), LLM Providers (at least one required), CRM Integrations (optional), Data Enrichment (optional), Email (optional), Notifications (optional), Observability (optional), Frontend, and Enterprise (optional).

### 17.2 Makefile Targets

setup (install deps + copy .env), dev (docker-compose up with watch mode), test (pytest + jest), lint (ruff + eslint), migrate (alembic upgrade head), seed (create test org + sample data), help (describe all targets).

---

## 18. BUILD PHASES WITH EXACT DELIVERABLES

### Phase 0 — Scaffolding (Days 1-3)
**Build:** Repo, Docker setup, all empty files in structure, CI pipeline, health endpoint.
**Done when:** `git clone` → `cp .env.example .env` → fill one LLM key → `docker-compose up` → `localhost:8000/health` returns `{"status": "ok", "postgres": "connected", "redis": "connected", "qdrant": "connected"}`.

### Phase 1 — ICP + Outbound MVP (Weeks 1-4)
**Build:** Auth (login, JWT, RBAC), ICP Agent (train + score), Outbound Agent (3 variations), Approval Queue (API + UI), Lead import (CSV + manual), Audit log viewer.
**Done when:** Upload CSV → train ICP with 5 customers → score all leads → generate outbound for high-score lead → review 3 variations in approval queue → approve one → see it in audit log.

### Phase 2 — Enrichment Layer (Weeks 5-7)
**Build:** Apollo.io enrichment, HubSpot CRM sync (bidirectional), Celery scheduled tasks, Enrichment status UI.
**Done when:** Connect HubSpot → contacts sync automatically → enrichment runs daily → ICP scores reflect enrichment → CRM custom properties update with scores.

### Phase 3 — Full Agent Suite (Weeks 8-13)
**Build:** Content Agent, Deal Intel Agent, Retention Agent, Slack notifications, Agent-to-agent communication, transcript ingestion.
**Done when:** All 5 agents functional. Deal risk alerts fire on Slack when risk > 0.75. Retention alerts on state degradation. Content agent passes quality flags.

### Phase 4 — Orchestrator + Dashboard (Weeks 14-17)
**Build:** LangGraph orchestrator (4 workflows), analytics dashboard (4 tabs), onboarding wizard, settings UI, notification center.
**Done when:** New user completes onboarding wizard → connects CRM → trains ICP → first scoring run → results visible in analytics dashboard. Weekly review runs automatically.

### Phase 5 — Open Source Launch (Weeks 18-19)
**Build:** README with screenshots, docs site, contributing guide, demo instance at gtm-engine.artifex.ai, HN + ProductHunt posts.
**Done when:** A developer goes from zero to running instance in under 10 minutes. README has 5+ screenshots. Docs cover every config option.

---

*This document is the complete engineering specification for the AI GTM Engine. Every file, every function, every error path, every security boundary, every data flow. Build in phase order. Ship each phase before starting the next.*

**Repository:** `github.com/artifex-hq/gtm-engine`
**Author:** Sai Sohan Merugu (Artifex, Hyderabad)
**Contact:** kalyaankummer@gmail.com
