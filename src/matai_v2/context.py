from typing import Optional

from openai import OpenAI

from matai_v2.configuration import Config
from matai_v2.email import EmailClientInterface, O365Account, O365EmailClient
from matai_v2.store import EmailStore
from matai_v2.trello import TrelloClient
import logging

logger = logging.getLogger(__name__)


class ApplicationContext:
    """Application context to hold configuration and other state"""
    __slots__ = ('config', 'outlook_auth_client',
                 'outlook_email_client', 'llm_client', 'trello_client', 'store')

    def __init__(self, config: Config, auth_client: Optional[O365Account] = None,
                 outlook_email_client: Optional[EmailClientInterface] = None,
                 trello_client: Optional[TrelloClient] = None,
                 store: Optional[EmailStore] = None):
        self.config = config
        if auth_client:
            self.outlook_auth_client = auth_client
        else:
            self.outlook_auth_client: O365Account = O365Account(
                credentials=(
                    config.outlook_config.client_id, config.outlook_config.client_secret),
                tenant_id=config.outlook_config.tenant_id,
            )
        if not outlook_email_client:
            self.outlook_email_client: EmailClientInterface = O365EmailClient(
                self.outlook_auth_client)
        else:
            self.outlook_email_client = outlook_email_client

        if trello_client:
            self.trello_client: TrelloClient = trello_client
        else:
            self.trello_client: TrelloClient = TrelloClient(
                config.trello_config.api_key, config.trello_config.api_token)

        if store:
            self.store = store
        else:
            self.store = EmailStore(config.database.path)

        if config.llm_config.host:
            self.llm_client = OpenAI(api_key=config.llm_config.api_key,
                                     base_url=config.llm_config.host)
        else:
            self.llm_client = OpenAI(api_key=config.llm_config.api_key)

    @classmethod
    def init(cls, config: Config, auth_client: Optional[O365Account] = None,
             outlook_email_client: Optional[EmailClientInterface] = None,
             trello_client: Optional[TrelloClient] = None,
             store: Optional[EmailStore] = None) -> 'ApplicationContext':
        """Initialize application context with given configuration"""
        return cls(config, auth_client, outlook_email_client, trello_client, store)
