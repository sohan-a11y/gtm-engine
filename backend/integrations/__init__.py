from backend.integrations.crm.base_crm import BaseCRM
from backend.integrations.data.apollo import ApolloClient
from backend.integrations.data.hunter import HunterClient
from backend.integrations.email.base_email import BaseEmail
from backend.integrations.notifications.slack import SlackWebhookClient

__all__ = [
    "ApolloClient",
    "BaseCRM",
    "BaseEmail",
    "HunterClient",
    "SlackWebhookClient",
]
