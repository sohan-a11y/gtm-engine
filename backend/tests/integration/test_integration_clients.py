from __future__ import annotations

import asyncio

from backend.integrations.crm.hubspot import HubSpotCRM
from backend.integrations.data.apollo import ApolloClient
from backend.integrations.email.gmail import GmailEmailClient
from backend.integrations.notifications.slack import SlackWebhookClient


def test_stub_clients_return_structured_payloads():
    async def scenario():
        crm = HubSpotCRM(access_token="token")
        apollo = ApolloClient(api_key="key")
        email = GmailEmailClient(oauth_token="token", from_address="noreply@example.com")
        slack = SlackWebhookClient(webhook_url="https://example.invalid/webhook")

        contact_result = await crm.update_contact(external_id="123", data={"name": "Jane"})
        enrich_result = await apollo.enrich_contact(contact={"email": "jane@example.com"})
        email_result = await email.send_email(to="jane@example.com", subject="Hello", body="Test")
        slack_result = await slack.send_message(text="Inbound review needed")

        assert contact_result["provider"] == "hubspot"
        assert "data" in enrich_result
        assert email_result["status"] == "queued"
        assert slack_result["status"] == "queued"

    asyncio.run(scenario())
