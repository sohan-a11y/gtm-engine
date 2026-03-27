# AI Agents

The engine ships five autonomous AI agents. Each agent drafts; humans approve. Nothing sends or changes CRM data without an explicit click in the approval queue.

---

## 1. ICP Scoring Agent

**File:** `backend/agents/icp_agent.py`

### What it does

Trains on your best customers and scores every new lead against that profile using vector similarity and LLM reasoning.

### Inputs

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Contact full name |
| `title` | string | Job title |
| `company` | string | Company name |
| `industry` | string | Industry vertical |
| `size` | string | Company headcount or ARR band |
| `pain_points` | string | Known pain points or notes |
| `notes` | string | Any additional context |

### Outputs

```json
{
  "score": 0.87,
  "explanation": "Strong fit: VP-level title, Series B SaaS, budget signals present.",
  "fit_signals": ["budget_available", "platform_fit"],
  "gap_signals": ["early_stage_risk"]
}
```

| Field | Range | Meaning |
|-------|-------|---------|
| `score` | 0.0 – 1.0 | Overall ICP fit |
| `fit_signals` | list | Positive signals found in the profile |
| `gap_signals` | list | Friction factors that reduce fit |

### Score interpretation

| Score | Badge | Action |
|-------|-------|--------|
| 0.75 – 1.00 | Green | High-priority outreach |
| 0.50 – 0.74 | Amber | Nurture sequence |
| 0.00 – 0.49 | Red | Deprioritize |

### How to train

The agent requires **at least 3 profiles** before scoring. Send your known-good customers:

```http
POST /agents/icp_agent/score
{
  "mode": "train",
  "profiles": [
    { "title": "VP of Sales", "company": "Acme", "industry": "SaaS", "size": "201-500" },
    { "title": "Head of Revenue", "company": "Beta Corp", "industry": "FinTech", "size": "51-200" },
    { "title": "CRO", "company": "Gamma Inc", "industry": "SaaS", "size": "501-1000" }
  ]
}
```

With fewer than 3 profiles the API returns `{ "status": "needs_more_profiles" }`. Train once, then score new leads one-by-one or in bulk via the UI.

---

## 2. Outbound Personalization Agent

**File:** `backend/agents/outbound_agent.py`

### What it does

For each lead in a campaign, generates **3 email variations**, each anchored to a different personalization hook. All three land in the approval queue — nothing sends until a human clicks Approve.

### Hook types

| Hook | Description |
|------|-------------|
| `pain_point` | Opens with a known pain the contact faces |
| `recent_news` | References a recent company event or funding round |
| `job_posting` | Infers intent from a role the company is hiring for |
| `tech_stack_change` | Notes a recent tool adoption or migration signal |

### Output per variation

```json
{
  "subject": "Quick idea for Acme",
  "body": "Hi Sarah, I noticed Acme is hiring three AEs...",
  "hook_type": "job_posting",
  "confidence": 0.81
}
```

### Validation flags

The agent auto-validates each variation before queuing it:

| Flag | Meaning |
|------|---------|
| `over_length` | Body exceeds 150 words |
| `mentions_ai` | Body explicitly mentions AI (auto-redacted) |
| `missing_cta` | No question mark detected — CTA appended automatically |

### Approval workflow

1. Agent generates 3 variations and creates 3 approval items (status: `pending`).
2. Reviewer opens the queue at `/approvals`.
3. For each item: edit inline if needed, then click **Approve** or **Reject**.
4. Approved items trigger the email send (Gmail or Outlook OAuth) and mark the lead as contacted in the CRM.

---

## 3. Deal Intelligence Agent

**File:** `backend/agents/deal_intel_agent.py`

### What it does

Analyzes CRM deal stage data, email thread summaries, call transcripts, and engagement metrics to produce a risk score and recommended actions. Fires a Slack alert when `risk_score >= 0.75`.

### Inputs

| Field | Description |
|-------|-------------|
| `deal` | CRM deal object (stage, amount, days in stage, close date) |
| `transcript_summary` | Optional: summary of latest call transcript |
| `engagement_metrics` | Optional: `reply_rate`, `email_opens`, `meeting_count` |
| `competitor_mentions` | Optional: list of competitor names detected |

### Risk scoring rubric

| Factor | Weight | Signal |
|--------|--------|--------|
| Days stalled in current stage | High | `> 30 days` adds significant risk |
| Deal size | Medium | Large deals (`> $10k`) are harder to close |
| Engagement reply rate | Negative (reduces risk) | `> 20%` reply rate is positive |
| Competitor mentions | Medium | Any competitor mention elevates risk |

### Risk levels

| Score | Level | Action |
|-------|-------|--------|
| 0.80 – 1.00 | `critical` | Slack alert fired immediately |
| 0.60 – 0.79 | `high` | Appears red in pipeline kanban |
| 0.40 – 0.59 | `medium` | Amber indicator |
| 0.00 – 0.39 | `low` | No alert |

### How to trigger

```http
POST /deals/{deal_id}/risk
```

Or let the scheduler run it automatically — the Celery beat schedule runs deal intelligence on all open deals every 6 hours.

### Slack alert threshold

Set `SLACK_WEBHOOK_URL` in `.env`. Alerts fire when `risk_score >= 0.75` or when a deal transitions to `critical`. See [integrations.md](integrations.md) for webhook setup.

---

## 4. Retention Analysis Agent

**File:** `backend/agents/retention_agent.py`

### What it does

Classifies each customer account into one of five health states, identifies the primary churn driver, and maps it to a Customer Success playbook.

### Health states

| State | Score Range | Playbook |
|-------|-------------|----------|
| **Thriving** | 0.80 – 1.00 | `expand_and_upsell` — proactively discuss expansion |
| **Stable** | 0.60 – 0.79 | `maintain_success_plan` — regular QBR cadence |
| **At Risk** | 0.40 – 0.59 | `focused_success_review` — scheduled review call within 2 weeks |
| **In Danger** | 0.20 – 0.39 | `escalated_intervention` — CSM escalation + exec sponsor outreach |
| **Critical** | 0.00 – 0.19 | `executive_save_plan` — red-account process, C-suite involvement |

### Churn driver signals

| Driver | Trigger |
|--------|---------|
| `support_issues` | More than 5 open support tickets |
| `low_usage` | Feature adoption rate below 30% |
| `champion_left` | Key contact marked as departed |
| `budget_concerns` | No other signal present — default |

### Output

```json
{
  "health_score": 0.38,
  "health_state": "In Danger",
  "churn_driver": "low_usage",
  "playbook": "escalated_intervention",
  "renewal_probability": 0.42,
  "state_transition": "stable_to_in_danger",
  "alert_required": true,
  "signals": ["usage_down", "tickets_up"]
}
```

`alert_required` is `true` when `health_score < 0.4` or when the account has degraded from its previous score. An alert generates an approval item in the queue for the CSM to review.

---

## 5. Content Generation Agent

**File:** `backend/agents/content_agent.py`

### What it does

Generates marketing content in three modes. All output respects the brand voice configured in Settings and is checked against quality flags before entering the approval queue.

### Modes

| Mode | Description | Typical length |
|------|-------------|----------------|
| `SEO_BLOG_POST` | Long-form article with search intent, product education, and a clear CTA | 600–900 words |
| `EMAIL_SEQUENCE` | Multi-step nurture sequence with subject lines and value progression | 3–5 emails |
| `LINKEDIN_POST` | Thought-leadership post with a concrete lesson and engagement question | 150–300 words |

### Quality flags

The agent auto-checks each draft and attaches flags before queuing it for approval:

| Flag | Trigger |
|------|---------|
| `over_length` | Body exceeds 900 words |
| `weak_cta` | No question mark in the draft |
| `too_salesy` | Contains phrases like "buy now", "best-in-class", "revolutionary" |
| `missing_hook` | No "because", "why", "how", or "for example" in the body |

Reviewers can see the flags in the approval queue before approving.

### API example

```http
POST /agents/content_agent/run
{
  "mode": "SEO_BLOG_POST",
  "topic": "How to reduce CAC with AI-driven ICP scoring",
  "brand_voice": "Direct, data-driven, no buzzwords",
  "context": { "target_persona": "VP Sales", "product": "GTM Engine" }
}
```
