#!/usr/bin/env python3
import click
import sqlite3
import yaml
import os
from matai.dao.interface import EmailContentDAO
import matai.dao.sqlite as dao
from matai.manager.sqlite_dao import SQLiteExecutionReportDAO
from configuration.configuration_service import ConfigurationService, FileConfigStorage
from configuration.configuration_service import ConfigurationService, FileConfigStorage
from configuration.application_configuration import ApplicationContext
from matai.commands.process_new_emails_command import ProcessNewEmailsCommand

DB_PATH = "pmai_sqlite.db"


def init_daos():
    conn = sqlite3.connect(DB_PATH)
    return dao.SQLiteActionItemDAO(conn), dao.SQLiteEmailContentDAO(conn), SQLiteExecutionReportDAO(conn)


@click.group()
@click.pass_context
def cli(ctx):
    """Lightweight CLI to view the application database."""

    configuration_path = os.getenv('PMAI_CONFIG_PATH', './config/config.yaml')
    try:
        service = ConfigurationService(FileConfigStorage(configuration_path))
        config = service.retrieve()
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


@cli.command("list-action-items")
@click.pass_context
def list_action_items(ctx):
    """List pending action items."""
    ctx_app = ctx.obj["app_ctx"]
    action_items = ctx_app.action_item_dao.list_action_items()
    if action_items:
        click.echo("Pending Action Items:")
        for i, ai in enumerate(action_items):
            click.echo(f"Action Item {i + 1}:")
            click.echo(str(ai))
    else:
        click.echo("No pending action items.")


@cli.command("list-emails")
@click.pass_context
def list_emails_cmd(ctx):
    """List stored emails."""
    ctx_app = ctx.obj["app_ctx"]
    emails = ctx_app.email_content_dao.list_email_contents()
    if emails:
        click.echo("Stored Emails:")
        for idx, email in enumerate(emails, start=1):
            click.echo(f"{idx}: Message Subject: {email.subject}")
            click.echo(f"\t ID: {email.message_id}")
            click.echo(f"\t Subject: {email.subject}")
            click.echo(f"\t Sender: {email.sender.to_string()}")
            click.echo(f"\t Timestamp: {email.timestamp}")
    else:
        click.echo("No emails stored.")


@cli.command("show-email")
@click.argument("id")
@click.pass_context
def show_email_cmd(ctx, id):
    """Show full details of a selected email."""
    ctx_app = ctx.obj["app_ctx"]
    email = ctx_app.email_content_dao.get_email_content(id)
    if email:
        click.echo("Email Details:")
        click.echo(str(email))
    else:
        click.echo(f"No email found with Message ID: {id}")


@cli.command("config")
@click.option('--verify', type=click.Path(exists=True), help='Verify a configuration file')
def verify_config(verify):
    """Verify a configuration file for correctness."""
    if not verify:
        click.echo("Please specify a configuration file to verify with --verify")
        return

    try:
        service = ConfigurationService(FileConfigStorage(verify))
        config = service.retrieve()
        click.echo("Configuration file is valid. Parsed configuration:")
        click.echo(yaml.dump(config.to_dict(), default_flow_style=False))
    except FileNotFoundError:
        click.echo(f"Error: Configuration file '{verify}' not found")
    except yaml.YAMLError as e:
        click.echo(f"Error: Invalid YAML format in configuration file:\n{e}")
    except Exception as e:
        click.echo(f"Error: Failed to parse configuration:\n{e}")


@cli.command("run-history")
@click.argument("num", type=int, default=5)
@click.pass_context
def show_run_history_cmd(ctx, num):
    """Show the last N runs of the application."""
    ctx_app = ctx.obj["app_ctx"]
    reports = ctx_app.execution_report_dao.retrieve_last(num)
    if reports:
        click.echo("Execution Reports:")
        for idx, report in enumerate(reports, start=1):
            click.echo(f"Report {idx}:")
            click.echo(str(report))
    else:
        click.echo("No execution reports found.")


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


@cli.command("run")
@click.pass_context
def run_command(ctx):
    """Run processing of new emails using ProcessNewEmailsCommand."""

    ctx_app = ctx.obj["app_ctx"]
    config = ctx.obj["app_config"]

    if not ctx_app.outlook_auth_client.is_authenticated:
        click.echo("Please authenticate first.")
        return

    command = ProcessNewEmailsCommand(
        run_configuration_dao=ctx_app.run_configuration_dao,
        email_manager=ctx_app.email_manager,
        filters=config.filters,
        integration_manager=ctx_app.integration_manager,
        execution_report_dao=ctx_app.execution_report_dao,
        confidence_level=config.confidence_level
    )
    command.execute()
    click.echo("New emails processed successfully.")


if __name__ == "__main__":
    cli()
