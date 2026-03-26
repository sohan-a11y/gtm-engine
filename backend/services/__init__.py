from .analytics_service import AnalyticsService
from .approval_service import ApprovalService
from .campaign_service import CampaignService
from .company_service import CompanyService
from .deal_service import DealService
from .integration_service import IntegrationService
from .settings_service import SettingsService
from .lead_service import LeadService
from .user_service import UserService

analytics_service = AnalyticsService()
approval_service = ApprovalService()
campaign_service = CampaignService()
company_service = CompanyService()
deal_service = DealService()
integration_service = IntegrationService()
lead_service = LeadService()
settings_service = SettingsService()
user_service = UserService()
