
import logging
import sqlite3
from dataclasses import dataclass
from openai import OpenAI
from supabase import Client, create_client
from typing import Tuple

from configuration import BoardConfig, Config, DatabaseConfig, EmailConfig, OutlookConfig, TrelloConfig
from matai.dao.interface import ActionItemDAO, EmailContentDAO, ParticipantDAO
from matai.dao.sqlite.sqlite_dao import (
    SQLiteActionItemDAO,
    SQLiteEmailContentDAO,
    SQLiteParticipantDAO,
)
from matai.email_client.interface import EmailClientInterface
from matai.email_client.o365_client import O365Account, O365EmailClient
from matai.email_processing.processor import EmailProcessor
from matai.integrations.integration_manager import IntegrationManager
from matai.integrations.trello import TrelloClient
from matai.manager.dao import ExecutionReportDAO, RunConfigurationDAO
from matai.manager.manager import EmailManager
from matai.manager.sqlite_dao import SQLiteExecutionReportDAO, SQliteRunConfigurationDAO

logger = logging.getLogger(__name__)


def initDAOs(database_config: DatabaseConfig) -> tuple[ActionItemDAO, EmailContentDAO, ParticipantDAO, RunConfigurationDAO, ExecutionReportDAO]:
    if database_config.name == "sqlite":
        db_path = database_config.host if database_config.host else "pmai_sqlite.db"
        conn = sqlite3.connect(db_path)
        db_init_scripts = "db/init_db_sqlite.sql"
        logger.info(
            "Initializing SQLite database with init scripts at %s", db_init_scripts)
        with open(db_init_scripts, "r") as f:
            logger.info("Executing init scripts")
            conn.executescript(f.read())
        action_item_dao = SQLiteActionItemDAO(conn)
        email_content_dao = SQLiteEmailContentDAO(conn)
        participant_dao = SQLiteParticipantDAO(conn)
        run_configuration_dao = SQliteRunConfigurationDAO(conn)
        execution_report_dao = SQLiteExecutionReportDAO(conn)
    else:
        raise ValueError(f"Unsupported database config: {database_config.name}")

    return action_item_dao, email_content_dao, participant_dao, run_configuration_dao, execution_report_dao

def initIntegrationManager(board_config: BoardConfig) -> IntegrationManager:
    if board_config.name.upper() == 'TRELLO':
        assert isinstance(
            board_config, TrelloConfig), "Board config is not a TrelloConfig"
        trello_client = TrelloClient(board_config.api_key, board_config.api_token)
        return IntegrationManager(trello_client, board_config.board)
    raise ValueError(f"Unsupported board config: {board_config}")


def initEmailClient(email_config: EmailConfig) -> Tuple[EmailClientInterface, O365Account]:
    # Initialize email client
    if email_config.name.upper() == 'OUTLOOK':
        assert isinstance(
            email_config, OutlookConfig), "Email config is not an OutlookConfig"
        credentials = (email_config.client_id, email_config.client_secret)
        tenant_id = email_config.tenant_id
        client = O365Account(credentials, tenant_id)
        return O365EmailClient(client), client
    raise ValueError(f"Unsupported email config: {email_config}")


@dataclass
class ApplicationContext:
    """Singleton class for managing application context"""
    action_item_dao: ActionItemDAO
    email_content_dao: EmailContentDAO
    participant_dao: ParticipantDAO
    run_configuration_dao: RunConfigurationDAO
    execution_report_dao: ExecutionReportDAO
    email_client: EmailClientInterface
    outlook_auth_client: O365Account
    email_processor: EmailProcessor
    email_manager: EmailManager
    integration_manager: IntegrationManager
    configuration:Config

    _instance = None


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def is_configuration_changed(self, configuration: Config) -> bool:
        """Check if the configuration has changed since the last initialization."""
        return self.configuration != configuration

    @classmethod
    def init(cls, configuration: Config) -> 'ApplicationContext':
        """Initialize or retrieve the ApplicationContext singleton.

        Args:
            configuration: Config object containing application settings

        Returns:
            ApplicationContext: The singleton instance, either newly created or existing
        """
        if cls._instance is not None and not cls._instance.is_configuration_changed(configuration):
            logger.info("Reusing existing ApplicationContext")
            return cls._instance
        elif cls._instance is not None:
            logger.info("Configuration has changed. Reinitializing ApplicationContext")

        action_item_dao, email_content_dao, participant_dao, run_configuration_dao, execution_report_dao = initDAOs(
            configuration.database)
        email_client, o365_client = initEmailClient(configuration.email['outlook'])

        if configuration.llm_config.host:
            processor = EmailProcessor(
                client=OpenAI(api_key=configuration.llm_config.api_key, base_url=configuration.llm_config.host),
                model=configuration.llm_config.model if configuration.llm_config.model else "gpt-4o",
                confidence_threshold=configuration.confidence_level)
        else:
            processor = EmailProcessor(
                client=OpenAI(api_key=configuration.llm_config.api_key),
                model=configuration.llm_config.model if configuration.llm_config.model else "gpt-4o",
                confidence_threshold=configuration.confidence_level)

        email_manager = EmailManager(email_client,
                                     action_item_dao,
                                     email_content_dao,
                                     processor,
                                     participant_dao)

        integration_manager = initIntegrationManager(configuration.board["trello"])
        return cls(action_item_dao,
                   email_content_dao,
                   participant_dao,
                   run_configuration_dao,
                   execution_report_dao,
                   email_client,
                   o365_client,
                   processor,
                   email_manager, 
                   integration_manager,
                   configuration)
