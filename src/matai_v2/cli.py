import click
import yaml
import os

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

    app_ctx = ApplicationContext.init(config)

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

