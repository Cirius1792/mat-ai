from typing import Optional

from matai_v2.configuration import Config
from matai_v2.email import EmailClientInterface, O365Account, O365EmailClient


class ApplicationContext:
    """Application context to hold configuration and other state"""

    def __init__(self, config: Config, auth_client: Optional[O365Account] = None):
        self.config = config
        if auth_client:
            self.outlook_auth_client = auth_client
        else:
            self.outlook_auth_client: O365Account = O365Account(
                credentials=(
                    config.outlook_config.client_id, config.outlook_config.client_secret),
                tenant_id=config.outlook_config.tenant_id,
            )
        self.outlook_email_client: EmailClientInterface = O365EmailClient(
            self.outlook_auth_client)

    @classmethod
    def init(cls, config: Config, auth_client: Optional[O365Account] = None) -> 'ApplicationContext':
        """Initialize application context with given configuration"""
        return cls(config, auth_client)


