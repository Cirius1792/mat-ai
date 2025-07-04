import click
import yaml
import os
import logging
from datetime import datetime, timedelta

from matai_v2.configuration import create_sample_config, load_config_from_yaml, save_config_to_yaml
from matai_v2.context import ApplicationContext
from matai_v2.logging import configure_logging
from matai_v2.parser import clean_body
from matai_v2.trello import TrelloBoardManager
configure_logging()
logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """Lightweight CLI to view the application database."""
    ctx.ensure_object(dict)
    if "app_ctx" in ctx.obj:
        return

    configuration_path = os.getenv('PMAI_CONFIG_PATH', './config/config.yaml')
    try:
        logger.info("Loading configuration from %s", configuration_path)
        config = load_config_from_yaml(configuration_path)
        logger.info("Configuration loaded successfully")
    except FileNotFoundError:
        click.echo("Error: Configuration file not found.")
        config = create_sample_config()
        save_config_to_yaml(config, configuration_path)
        click.echo("Sample configuration created at " + configuration_path)
        return
    except yaml.YAMLError as e:
        click.echo("Error: Invalid configuration format. " + str(e))
        return

    app_ctx: ApplicationContext = ApplicationContext.init(config)

    ctx.obj = {
        "app_ctx": app_ctx,
        "app_config": config,
    }


@cli.command("authenticate")
@click.pass_context
def authenticate_command(ctx):
    """Authenticate the application with the email server."""

    if "app_ctx" not in ctx.obj:
        click.echo("Application context not initialized. ")
        return

    ctx_app = ctx.obj["app_ctx"]
    if ctx_app.outlook_auth_client.is_authenticated:
        click.echo("Already authenticated")
        return

    auth_link, _ = ctx_app.outlook_auth_client.get_auth_link()
    click.echo("Please visit this URL to authenticate:")
    click.echo(auth_link)
    click.echo("After authentication, paste the URL you were redirected to below:")
    token_input = input("Authentication URL: ")
    result = ctx_app.outlook_auth_client.complete_authentication(token_input)
    if result:
        click.echo(
            "Authentication completed successfully")
    else:
        click.echo("Authentication failed. Please try again.")


@cli.command("run", short_help="Run the application to process new emails")
@click.argument("days", type=int, default=2)
@click.pass_context
def run(ctx, days):
    """Run the application processing the new emails not already processed and storing the identified action item on the given board. 
    The emails are retrieved in the last n days, where n can be configured by passing the appropriate parameter. If no configuration is provided, the emails in the last 2 days are analysed. 
    """
    ctx_app: ApplicationContext = ctx.obj["app_ctx"]
    if not ctx_app.outlook_auth_client.is_authenticated:
        click.echo("Please authenticate first using the 'authenticate' command.")
        return
    try:

        # Initialize the Trello board manager with the configured Trello client and board
        trello_manager = TrelloBoardManager(
            ctx_app.trello_client, ctx_app.config.trello_config.board)
        trello_manager.setup()

        # Calculate the start date taking the current date time and then subtracting the days variable
        click.echo(f"Processing emails from the last {days} days...")
        start_date = datetime.now() - timedelta(days=days)

        # Retrieve emails from the Outlook client
        emails = ctx_app.outlook_email_client.read_messages(
            start_date=start_date)
        # Filter email to avoid already processed once
        processed_emails_store = ctx_app.store
        processed_emails = {
            m.message_id for m in processed_emails_store.retrieve_from(start_date)}
        for email in filter(lambda m: m.message_id not in processed_emails, emails):
            click.echo(
                f"Processing email: {email.subject} from {email.sender}")
            # Cleaning Email body from html tag and previous messages
            cleaned_body = clean_body(email.body)
            # Process each email to identify action items
            action_items = ctx_app.processor.process_email(email.message_id,
                                                           email.subject,
                                                           email.sender.email,
                                                           [recipient.email for recipient in email.recipients],
                                                           email.timestamp,
                                                           cleaned_body)
            # Store action items into the trello board
            trello_manager.create_tasks(
                email.subject, cleaned_body, action_items)

            # Store the id of the processed email
            processed_emails_store.store(
                email.message_id, email.timestamp, 'PROCESSED')

    except Exception as e:
        click.echo(f"Error running the application: {e}")
