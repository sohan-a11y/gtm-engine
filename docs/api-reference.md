# API Reference

Base URL: `http://localhost:8000` (development) or `https://yourdomain.com/api` (production via Nginx).

All endpoints except `/auth/register` and `/auth/login` require a Bearer token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

All responses use `Content-Type: application/json`. Errors follow this envelope:
```json
{ "detail": "human-readable message", "code": "snake_case_code", "status_code": 422 }
```

---

## Authentication

### `POST /auth/register`

Create a new user and organization.

**Request:**
```json
{
  "email": "you@example.com",
  "password": "securepassword",
  "full_name": "Jane Doe",
  "org_name": "Acme Corp",
  "role": "admin"
}
```

**Response:** `AuthSessionResponse` with `access_token`, `refresh_token`, and `user` object.

---

### `POST /auth/login`

Exchange email/password for tokens.

**Request:**
```json
{ "email": "you@example.com", "password": "securepassword" }
```

**Response:** Same `AuthSessionResponse` shape as register.

---

### `POST /auth/refresh`

Exchange a refresh token for a new access token.

**Request:**
```json
{ "refresh_token": "<refresh_token>" }
```

---

### `POST /auth/logout`

Invalidate the current session. Requires Bearer token.

---

## Leads

### `GET /leads`

List all leads for the authenticated org, paginated.

**Query params:** `page` (default 1), `page_size` (default 20).

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

---

### `POST /leads`

Create a single lead.

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@acme.com",
  "company_name": "Acme Corp",
  "title": "VP of Sales",
  "industry": "SaaS"
}
```

---

### `POST /leads/import`

Bulk import leads from CSV or JSON.

**Multipart form:**
- `upload`: CSV file with header row matching `LeadCreate` field names, or
- `rows`: JSON string of a single `LeadCreate` object

**Response:**
```json
{ "imported": 42, "failed": 2, "errors": ["row 5: invalid email"] }
```

---

### `POST /leads/{lead_id}/score`

Trigger the ICP Scoring Agent for a single lead. Returns immediately with the updated lead including the new `icp_score` field.

---

## Campaigns

### `GET /campaigns`

List all campaigns for the org.

### `POST /campaigns`

Create a new campaign.

**Request:**
```json
{
  "name": "Q2 SaaS Outbound",
  "value_prop": "Reduce GTM tool spend by 60%",
  "target_industry": "SaaS",
  "target_titles": ["VP Sales", "CRO", "Head of Revenue"]
}
```

### `POST /campaigns/{campaign_id}/generate`

Trigger the Outbound Personalization Agent for all leads assigned to this campaign. Generates 3 email variations per lead and adds them to the approval queue.

---

## Deals

### `GET /deals`

List all deals for the org. Query params: `stage`, `page`, `page_size`.

### `POST /deals`

Create a deal manually (deals are also synced from CRM automatically).

**Request:**
```json
{
  "name": "Acme Enterprise",
  "amount_cents": 120000,
  "stage": "Proposal",
  "close_date": "2026-06-30",
  "company_id": "<uuid>"
}
```

### `POST /deals/{deal_id}/risk`

Trigger the Deal Intelligence Agent for a specific deal. Returns updated deal with `risk_score` and `risk_level`.

**Optional request body:**
```json
{
  "transcript_summary": "Champion confirmed budget. Legal reviewing MSA.",
  "engagement_metrics": { "reply_rate": 0.35, "meeting_count": 4 },
  "competitor_mentions": ["Outreach", "Salesloft"]
}
```

---

## Approvals

### `GET /approvals`

List pending approval items. Query params: `page`, `page_size`.

**Response:**
```json
{
  "items": [
    {
      "id": "<uuid>",
      "type": "outbound_email",
      "status": "pending",
      "content": { "subject": "...", "body": "..." },
      "lead_id": "<uuid>",
      "created_at": "2026-03-27T12:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 20
}
```

---

### `POST /approvals/{approval_id}/approve`

Approve an item. For email variations, this triggers the send via the connected email provider.

**Request (optional):**
```json
{ "notes": "Approved with minor edit" }
```

---

### `POST /approvals/{approval_id}/reject`

Reject an item and remove it from the queue.

**Request (optional):**
```json
{ "notes": "Tone doesn't match brand voice" }
```

---

## Analytics

All analytics endpoints require the Bearer token and are scoped to the authenticated org.

### `GET /analytics/summary`

Returns a top-level dashboard summary:
```json
{
  "leads_scored_today": 14,
  "emails_generated_today": 42,
  "pipeline_value_usd": 840000,
  "accounts_at_risk": 3
}
```

### `GET /analytics/pipeline`

Pipeline metrics: deal count and value by stage, win rate, average deal size.

### `GET /analytics/outbound`

Outbound metrics: emails generated, approved, sent, reply rate, open rate.

### `GET /analytics/retention`

Retention metrics: account health distribution, churn risk value, renewals in next 30/60/90 days.

### `GET /analytics/usage`

Full `AnalyticsOverview` combining all four metric groups plus LLM cost tracking (tokens consumed, estimated spend by provider and model).

---

## Settings

### `GET /settings`

Get the org's current settings (CRM config, notification preferences, feature flags).

### `PATCH /settings`

Update org settings. Send only the fields you want to change.

### `GET /settings/llm-config`

Get the active LLM provider and model configuration.

### `PATCH /settings/llm-config`

Update LLM configuration:
```json
{
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "embedding_model": "text-embedding-3-small"
}
```

### `GET /settings/brand-voice`

Get the brand voice configuration used by the Content and Outbound agents.

### `PATCH /settings/brand-voice`

Update brand voice:
```json
{
  "tone": "Direct and data-driven",
  "avoid": ["buzzwords", "jargon", "passive voice"],
  "examples": ["We help teams ship faster.", "Here is what we found in the data."]
}
```

---

## Health

### `GET /health`

Returns `200 OK` when the API is ready. Used by Docker Compose and Railway health checks.

```json
{ "status": "healthy", "version": "0.1.0" }
```
