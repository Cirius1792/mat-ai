#!/usr/bin/env python3
import click
import sqlite3
import yaml
from matai.dao.interface import EmailContentDAO
import matai.dao.sqlite as dao
from matai.manager.sqlite_dao import SQLiteExecutionReportDAO
from configuration import Config

DB_PATH = "pmai_sqlite.db"


def init_daos():
    conn = sqlite3.connect(DB_PATH)
    return dao.SQLiteActionItemDAO(conn), dao.SQLiteEmailContentDAO(conn), SQLiteExecutionReportDAO(conn)


@click.group()
@click.pass_context
def cli(ctx):
    """Lightweight CLI to view the application database."""
    action_item_dao, email_content_dao, execution_report_dao = init_daos()
    ctx.obj = {
        "action_item_dao": action_item_dao,
        "email_content_dao": email_content_dao,
        "execution_report_dao": execution_report_dao,
    }


@cli.command("list-action-items")
@click.pass_context
def list_action_items(ctx):
    """List pending action items."""
    action_item_dao = ctx.obj["action_item_dao"]
    action_items = action_item_dao.list_action_items()
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
    email_content_dao: EmailContentDAO = ctx.obj["email_content_dao"]
    emails = email_content_dao.list_email_contents()
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
    email_content_dao = ctx.obj["email_content_dao"]
    email = email_content_dao.get_email_content(id)
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
        config = Config.load_config_from_yaml(verify)
        click.echo("Configuration file is valid. Parsed configuration:")
        click.echo(yaml.dump(config.to_dict(), default_flow_style=False))
    except FileNotFoundError:
        click.echo(f"Error: Configuration file '{verify}' not found")
    except yaml.YAMLError as e:
        click.echo(f"Error: Invalid YAML format in configuration file:\n{e}")
    except Exception as e:
        click.echo(f"Error: Failed to parse configuration:\n{e}")


@cli.command("show-history")
@click.argument("num", type=int, default=5)
@click.pass_context
def show_run_history_cmd(ctx, num):
    """Show the last N runs of the application."""
    execution_report_dao = ctx.obj["execution_report_dao"]
    reports = execution_report_dao.retrieve_last(num)
    if reports:
        click.echo("Execution Reports:")
        for idx, report in enumerate(reports, start=1):
            click.echo(f"Report {idx}:")
            click.echo(str(report))
    else:
        click.echo("No execution reports found.")


@cli.command("run")
@click.pass_context
def run_command(ctx):
    """Run processing of new emails using ProcessNewEmailsCommand."""
    import os, yaml, click
    from configuration import Config
    configuration_path = os.getenv('PMAI_CONFIG_PATH', './config/config.yaml')
    try:
        config = Config.load_config_from_yaml(configuration_path)
    except FileNotFoundError:
        click.echo("Error: Configuration file not found.")
        return
    except yaml.YAMLError as e:
        click.echo("Error: Invalid configuration format. " + str(e))
        return

    from configuration.application_configuration import ApplicationContext
    ctx_app = ApplicationContext.init(config)

    from matai.commands.process_new_emails_command import ProcessNewEmailsCommand
    command = ProcessNewEmailsCommand(
         run_configuration_dao=ctx_app.run_configuration_dao,
         email_manager=ctx_app.email_manager,
         filters=config.filters,
         integration_manager=ctx_app.integration_manager,
         execution_report_dao=ctx_app.execution_report_dao,
         confidence_level=config.confidence_level
    )
    command.execute()
    click.echo("ProcessNewEmailsCommand executed successfully.")

if __name__ == "__main__":
    cli()
