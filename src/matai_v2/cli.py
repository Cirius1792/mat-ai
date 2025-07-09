import click
from openai import OpenAI
import yaml
import os
import logging
from datetime import datetime, timedelta

from matai_v2.benchmark import benchmark_model_from_dataset, load_judge_test_from_jsonl, print_benchmark_results, store_benchmark_results_to_markdown_file
from matai_v2.configuration import create_sample_config, load_config_from_yaml, save_config_to_yaml
from matai_v2.context import ApplicationContext
from matai_v2.logging import configure_logging
from matai_v2.parser import clean_body
from matai_v2.processor import process_email
from matai_v2.trello import TrelloBoardManager
configure_logging()
logger = logging.getLogger(__name__)


configuration_path = os.getenv('PMAI_CONFIG_PATH', './config/config.yaml')


@click.group()
@click.pass_context
def cli(ctx):
    """Lightweight CLI to view the application database."""
    ctx.ensure_object(dict)
    if "app_ctx" in ctx.obj:
        return

    try:
        logger.info("Loading configuration from %s", configuration_path)
        config = load_config_from_yaml(configuration_path)
        logger.info("Configuration loaded successfully")
    except FileNotFoundError:
        click.echo("Error: Configuration file not found.")
        # FIXME: create the required folders to store the configuration if they do not exists
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


@cli.command("authenticate", short_help="Set up the application authenticating with Outlook and Trello")
@click.pass_context
def authenticate_command(ctx):
    """Authenticate the application with the email server."""

    if "app_ctx" not in ctx.obj:
        click.echo("Application context not initialized. ")
        return

    ctx_app: ApplicationContext = ctx.obj["app_ctx"]
    if ctx_app.outlook_auth_client.is_authenticated:
        click.echo("Already authenticated with Outlook")
    else:
        auth_link, _ = ctx_app.outlook_auth_client.get_auth_link()
        click.echo("Outlook")
        click.echo("Please visit this URL to authenticate:")
        click.echo(auth_link)
        click.echo(
            "After authentication, paste the URL you were redirected to below:")
        token_input = input("Authentication URL: ")
        result = ctx_app.outlook_auth_client.complete_authentication(
            token_input)
        if result:
            click.echo(
                "Authentication completed successfully")
            click.echo()
        else:
            click.echo("Authentication failed. Please try again.")
            return
    app_config = ctx.obj["app_config"]
    if not app_config.trello_config.board:
        click.echo(
            "No Trello board configured. Retrieving available boards...")
        boards = ctx_app.trello_client.boards()
        prompt = "Please select a board by entering the corresponding number:\n"
        for i, board in enumerate(boards):
            prompt += f"{i + 1}. {board.name} \n"
        prompt += "Enter the number of the board you want to use: "
        chosen_board = click.prompt(prompt, type=int, default=1, show_default=False,
                                    show_choices=True, err=True)
        config = ctx_app.config
        config.trello_config.board = boards[chosen_board-1].id
        save_config_to_yaml(config, configuration_path)
        return


@cli.command("run", short_help="Run the application to process new emails")
@click.option("--days", "-d", type=int, default=2)
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

        # Calculate the start date taking the current date time and then subtracting the days variable
        click.echo(f"Processing emails from the last {days} days...")
        start_date = datetime.now() - timedelta(days=days)

        # Retrieve emails from the Outlook client
        emails = ctx_app.outlook_email_client.read_messages(
            start_date=start_date, filters=ctx_app.config.filters)
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
            action_items = process_email(
                ctx_app.llm_client,
                ctx_app.config.llm_config.model,
                email.message_id,
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


@cli.command("init", short_help="Initialize the application with a sample configuration")
@click.option("--config", type=click.Path(),
              default=lambda: os.getenv(
                  'PMAI_CONFIG_PATH', './config/config.yaml'),
              help="Path to the configuration file")
def init(config):
    """Initialize the application with a sample configuration."""
    try:
        logger.info("Creating sample configuration at %s", config)
        cfg = create_sample_config()
        save_config_to_yaml(cfg, config)
        click.echo("Sample configuration created at " + config)
    except Exception as e:
        click.echo(f"Error creating sample configuration: {e}")


@cli.command("benchmark-judge", short_help="Score an AI Judge with the given llm configuration against a known dataset")
@click.argument("test-file-path", type=click.Path(exists=True))
@click.option("--models", type=str, help="Comma-separated list of model identifiers to benchmark. If none is provided, the model configured in the config file will be used")
@click.option("--config", type=click.Path(),
              default=lambda: os.getenv(
                  'PMAI_CONFIG_PATH', './config/config.yaml'),
              help="Path to the configuration file")
@click.option("--output", type=str, default=None, help="Path to save the benchmark results")
def benchmark(test_file_path, models, config, output):
    cfg = load_config_from_yaml(config)
    # Assuming you have an OpenAI client configured
    llm_client = OpenAI(
        base_url=cfg.llm_config.host, api_key=cfg.llm_config.api_key)
    # Replace with your actual model identifier
    judge_model = [cfg.llm_config.model]
    if models:
        judge_model = models.split(',')
    results = benchmark_model_from_dataset(
        llm_client,
        judge_model,
        load_judge_test_from_jsonl(test_file_path)
    )
    print_benchmark_results(results, click.echo)
    if output is not None:
        store_benchmark_results_to_markdown_file(results, output)
