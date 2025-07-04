import click
import yaml
import os
from datetime import datetime, timedelta

from matai_v2.configuration import load_config_from_yaml
from matai_v2.context import ApplicationContext

@click.group()
@click.pass_context
def cli(ctx):
    """Lightweight CLI to view the application database."""
    if ctx.obj and "app_ctx" in ctx.obj:
        return

    configuration_path = os.getenv('PMAI_CONFIG_PATH', './config/config.yaml')
    try:
        config = load_config_from_yaml(configuration_path)
    except FileNotFoundError:
        click.echo("Error: Configuration file not found.")
        return
    except yaml.YAMLError as e:
        click.echo("Error: Invalid configuration format. " + str(e))
        return

    app_ctx:ApplicationContext = ApplicationContext.init(config)

    ctx.obj = {
        "app_ctx": app_ctx,
        "app_config": config,
    }


@cli.command("authenticate")
@click.pass_context
def authenticate_command(ctx):
    """Authenticate the application with the email server."""

    ctx_app = ctx.obj["app_ctx"]
    if ctx_app.outlook_auth_client.is_authenticated:
        click.echo("Already authenticated")
        return

    auth_link, flow = ctx_app.outlook_auth_client.get_auth_link()
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

@cli.command("run",short_help="Run the application to process new emails")
@click.argument("days", type=int, default=2)
@click.pass_context
def run(ctx, days):
    """Run the application processing the new emails not already processed and storing the identified action item on the given board. 
    The emails are retrieved in the last n days, where n can be configured by passing the appropriate parameter. If no configuration is provided, the emails in the last 2 days are analysed. 
    """
    ctx_app = ctx.obj["app_ctx"]
    if not ctx_app.outlook_auth_client.is_authenticated:
        click.echo("Please authenticate first using the 'authenticate' command.")
        return
    try:
        # Calculate the start date taking the current date time and then subtracting the days variable
        click.echo(f"Processing emails from the last {days} days...")
        start_days = datetime.now() - timedelta(days=days)

        # The test should verfy that this method has been invoked with a date that is 5 days before today AI
        ctx_app.email_client.read_messages(start_days=start_days)
    except Exception as e:
        click.echo(f"Error running the application: {e}")

