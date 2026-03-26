from . import agents, analytics, approvals, auth, campaigns, companies, deals, events, health, integrations, jobs, leads, settings, webhooks

ROUTERS = [
    auth.router,
    leads.router,
    companies.router,
    deals.router,
    campaigns.router,
    approvals.router,
    agents.router,
    analytics.router,
    integrations.router,
    settings.router,
    webhooks.router,
    jobs.router,
    events.router,
    health.router,
]

