import os
import time
import yaml
from configuration import Config, DatabaseConfig, FiltersConfig, OutlookConfig, TrelloConfig
from configuration.application_configuration import ApplicationContext
from dotenv import load_dotenv
import logging
from matai.common.logging import configure_logging
from matai.manager.manager import EmailFilters, ManagedEmails
from matai.manager.models import ExecutionReport, RunConfiguration, RunStatus

configure_logging(log_level='DEBUG')
logger = logging.getLogger(__name__)
load_dotenv("email.env")


def print_action(action_item):
    logger.debug(f"Action Item ID: {action_item.id}")
    logger.debug(f"Description: {action_item.description}")
    logger.debug(f"Type: {action_item.action_type.name}")
    logger.debug(f"Due Date: {action_item.due_date}")
    logger.debug(f"Confidence Score: {action_item.confidence_score}")
    logger.debug("-" * 40)


def print_email(email_content):
    logger.debug(f"Email ID: {email_content.message_id}")
    logger.debug(f"Subject: {email_content.subject}")
    logger.debug(f"From: {email_content.sender.to_string()}")
    logger.debug(
        f"To: {', '.join([recipient.to_string() for recipient in email_content.recipients])}")
    logger.debug(f"Timestamp: {email_content.timestamp}")


def build_execution_report(run_configuration: RunConfiguration,
                           managed_emails_num: int,
                           generated_action_items:int,
                           total_execution_time: float) -> ExecutionReport:

    assert run_configuration.configuration_id is not None, "Can't store an execution report without a valid run configuration"

    return ExecutionReport(
        configuration_id=run_configuration.configuration_id,
        run_status=RunStatus.SUCCESS,
        retrieved_emails=managed_emails_num,
        generated_action_items=generated_action_items,
        total_execution_time=total_execution_time
    )


# The execute_email_processing function has been removed.
# Use ProcessNewEmailsCommand in the main block instead.


if __name__ == "__main__":
    start_time = time.perf_counter()
    configuration_path = os.getenv('PMAI_CONFIG_PATH', './config/config.yaml')
    config = None
    try:
        config = Config.load_config_from_yaml(configuration_path)
        logger.debug("Loaded config from file: %s", config)
    except FileNotFoundError:
        logger.debug("No existing config found, creating new one")
        config = Config(DatabaseConfig(), {"outlook": OutlookConfig("Outlook")}, {
                        "trello": TrelloConfig("Trello")}, FiltersConfig())
    except yaml.YAMLError as e:
        logger.error("Failed to parse config file: %s", e)
        raise SystemExit("Cannot continue with invalid configuration file")

    assert config is not None, "Config is not set"
    ctx: ApplicationContext = ApplicationContext.init(config)
    from matai.commands.process_new_emails_command import ProcessNewEmailsCommand
    command = ProcessNewEmailsCommand(
        run_configuration_dao=ctx.run_configuration_dao,
        email_manager=ctx.email_manager,
        filters=ctx.configuration.filters,
        integration_manager=ctx.integration_manager,
        execution_report_dao=ctx.execution_report_dao,
        confidence_level=ctx.configuration.confidence_level
    )
    command.execute()
