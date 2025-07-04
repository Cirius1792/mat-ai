from typing import Optional

from openai import OpenAI

from matai_v2.configuration import Config
from matai_v2.email import EmailClientInterface, O365Account, O365EmailClient
from matai_v2.processor import EmailProcessor


class ApplicationContext:
    """Application context to hold configuration and other state"""
    __slots__ = ('config', 'outlook_auth_client', 'outlook_email_client', 'processor')

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

        if config.llm_config.host:
            llm_client = OpenAI(api_key=config.llm_config.api_key, base_url=config.llm_config.host)
        else: 
            llm_client = OpenAI(api_key=config.llm_config.api_key)
        self.processor: EmailProcessor= EmailProcessor(llm_client, self.config.llm_config.model)

    @classmethod
    def init(cls, config: Config, auth_client: Optional[O365Account] = None) -> 'ApplicationContext':
        """Initialize application context with given configuration"""
        return cls(config, auth_client)


