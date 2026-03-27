# Integrations

All integrations are optional. Agents fall back gracefully when credentials are absent. Credentials are encrypted at rest using AES-256 (Fernet) before being stored.

---

## HubSpot

### OAuth App Setup

1. Go to [developers.hubspot.com](https://developers.hubspot.com) and create a developer account.
2. Click **Create app** → give it a name (e.g. "GTM Engine").
3. Under **Auth**, copy the **Client ID** and **Client Secret** into `.env`:
   ```ini
   HUBSPOT_CLIENT_ID=<your-client-id>
   HUBSPOT_CLIENT_SECRET=<your-client-secret>
   HUBSPOT_REDIRECT_URI=https://yourdomain.com/integrations/hubspot/callback
   ```
4. Add the redirect URI to the app's **Redirect URLs** list.

### Required Scopes

| Scope | Purpose |
|-------|---------|
| `crm.objects.contacts.read` | Read contact records |
| `crm.objects.contacts.write` | Write ICP score and enrichment data back |
| `crm.objects.companies.read` | Read company records |
| `crm.objects.deals.read` | Read pipeline deals for deal intelligence |
| `crm.objects.deals.write` | Update deal risk score |

### What Syncs

The CRM sync runs every 4 hours (Celery beat schedule):

- **Inbound:** New contacts and deals are pulled into Postgres.
- **Outbound:** ICP score and enrichment fields are written back to HubSpot contact properties.

### Custom Properties Written Back

| HubSpot Property Name | Type | Value |
|-----------------------|------|-------|
| `gtm_icp_score` | Number (0–1) | ICP fit score |
| `gtm_icp_fit_signals` | Multi-line text | Comma-separated fit signals |
| `gtm_icp_gap_signals` | Multi-line text | Comma-separated gap signals |
| `gtm_last_scored_at` | DateTime | Timestamp of last scoring run |

---

## Salesforce

### Connected App Setup

1. In Salesforce, go to **Setup → App Manager → New Connected App**.
2. Enable **OAuth Settings**:
   - Callback URL: `https://yourdomain.com/integrations/salesforce/callback`
   - Selected OAuth Scopes: `api`, `refresh_token`, `offline_access`
3. After saving, copy the **Consumer Key** (Client ID) and **Consumer Secret** into `.env`:
   ```ini
   SALESFORCE_CLIENT_ID=<Consumer Key>
   SALESFORCE_CLIENT_SECRET=<Consumer Secret>
   ```

### OAuth Flow

1. In the app, go to **Settings → Integrations → Salesforce**.
2. Click **Connect**. You'll be redirected to Salesforce's OAuth consent screen.
3. After approval, the app stores the access and refresh tokens encrypted in Postgres.

### Field Mapping

| Salesforce Object | Salesforce Field | GTM Engine Field |
|-------------------|------------------|------------------|
| Contact | `Email` | `email` |
| Contact | `Title` | `title` |
| Contact | `Account.Name` | `company_name` |
| Opportunity | `StageName` | `deal_stage` |
| Opportunity | `Amount` | `amount_cents` (× 100) |
| Opportunity | `CloseDate` | `close_date` |
| Opportunity | `GTM_Risk_Score__c` | `risk_score` (written back) |

---

## Gmail

### GCP OAuth Credential Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create or select a project.
2. Enable the **Gmail API** under APIs & Services → Library.
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**.
   - Application type: **Web application**
   - Authorized redirect URIs: `https://yourdomain.com/integrations/gmail/callback`
4. Copy Client ID and Client Secret into `.env`:
   ```ini
   GMAIL_CLIENT_ID=<client-id>.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=<client-secret>
   GMAIL_REDIRECT_URI=https://yourdomain.com/integrations/gmail/callback
   ```

### Required Scopes

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/gmail.send` | Send approved emails |
| `https://www.googleapis.com/auth/gmail.readonly` | Read email thread context for personalization |

> **Note:** Google requires OAuth consent screen verification for apps accessing `gmail.send` in production. For internal/testing use, you can add test users without verification.

---

## Outlook / Microsoft 365

### Azure App Registration

1. Go to [portal.azure.com](https://portal.azure.com) → **Azure Active Directory → App registrations → New registration**.
2. Set **Name** (e.g. "GTM Engine") and **Supported account types** (single tenant or multi-tenant depending on your setup).
3. Under **Redirect URI**, select **Web** and enter:
   `https://yourdomain.com/integrations/outlook/callback`
4. After creation, go to **Certificates & secrets → New client secret**. Copy the **Value** (not the ID).
5. Copy the **Application (client) ID** from the Overview page.
6. Set in `.env`:
   ```ini
   OUTLOOK_CLIENT_ID=<Application (client) ID>
   OUTLOOK_CLIENT_SECRET=<client secret value>
   OUTLOOK_REDIRECT_URI=https://yourdomain.com/integrations/outlook/callback
   ```

### Required API Permissions (Microsoft Graph)

| Permission | Type | Purpose |
|------------|------|---------|
| `Mail.Send` | Delegated | Send approved emails |
| `Mail.ReadWrite` | Delegated | Read thread context |
| `offline_access` | Delegated | Refresh tokens without re-prompting |

Grant admin consent in the Azure portal after adding the permissions.

---

## Apollo.io

1. Log into [app.apollo.io](https://app.apollo.io).
2. Go to **Settings → Integrations → API Keys**.
3. Click **Create new key** and copy the value.
4. Set in `.env`:
   ```ini
   APOLLO_API_KEY=<your-api-key>
   ```

Apollo is used to enrich new leads with company size, funding stage, technology stack, and job title normalization. Enrichment runs automatically when a new lead is imported.

---

## Hunter.io

1. Log into [hunter.io](https://hunter.io) and go to **API → API Key**.
2. Copy the key and set:
   ```ini
   HUNTER_API_KEY=<your-api-key>
   ```

Hunter is used to verify email addresses and find additional contacts at target companies. It runs as a fallback enrichment step after Apollo.

---

## Slack

### Incoming Webhook URL Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app **From scratch**.
2. Under **Add features and functionality**, click **Incoming Webhooks** and toggle it on.
3. Click **Add New Webhook to Workspace** and select the channel for alerts (e.g. `#deal-alerts`).
4. Copy the webhook URL and set:
   ```ini
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
   ```

Slack alerts fire when:
- A deal's risk score exceeds `0.75` (Deal Intelligence Agent)
- An account transitions to **In Danger** or **Critical** health state (Retention Agent)

Alert messages include the deal/account name, score, primary risk factor, and a link to the relevant record in the GTM Engine UI.
