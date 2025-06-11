import click
from matai.benchmark.dataset import Dataset, DatasetLine
from matai.email_processing.model import EmailContent, ActionItem, EmailAddress, Participant, ActionType
from datetime import datetime
import uuid


@click.group()
def cli():
    """CLI to manage the benchmark dataset."""
    pass


@cli.command("show")
@click.option("--dataset-path", type=click.Path(), default="dataset.jsonl", help="Path to the dataset file")
def show(dataset_path):
    """Show entries in human-readable format with pagination."""
    dataset = Dataset(file_path=dataset_path)
    lines = dataset.load()
    if not lines:
        click.echo("No entries found.")
        return
    parts = []
    for idx, dl in enumerate(lines):
        parts.append(f"Entry {idx+1}/{len(lines)}")
        parts.append(str(dl.email))
        for ai in dl.expected_action_items:
            parts.append(str(ai))
            parts.append("")
        parts.append("")
    text = "\n\n".join(parts)
    click.echo_via_pager(text)


@cli.command("add")
@click.option("--dataset-path", type=click.Path(), default="dataset.jsonl", help="Path to the dataset file")
def add(dataset_path):
    """Add a new entry to the dataset."""
    # Email content phase
    click.echo("== Email Content Entry ==")
    message_id = click.prompt("Message ID", default="", show_default=False)
    if not message_id:
        message_id = str(uuid.uuid4())
    subject = click.prompt("Subject")
    sender_str = click.prompt("Sender (e.g. Name <email@domain.com>)")
    sender = EmailAddress.from_string(sender_str)
    recipients = []
    click.echo("Enter recipients (empty to finish):")
    while True:
        rec = click.prompt("Recipient", default="", show_default=False)
        if not rec:
            break
        recipients.append(EmailAddress.from_string(rec))
    thread_id = click.prompt("Thread ID", default="", show_default=False)
    if not thread_id:
        thread_id = str(uuid.uuid4())
    timestamp_str = click.prompt("Timestamp (YYYY-MM-DD HH:MM:SS or ISO)", default="")
    if timestamp_str:
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            timestamp = datetime.fromisoformat(timestamp_str)
    else:
        timestamp = datetime.now()
    body = click.edit(text="Enter email body:") or ""
    email = EmailContent(
        message_id=message_id,
        subject=subject,
        sender=sender,
        recipients=recipients,
        thread_id=thread_id,
        timestamp=timestamp,
        raw_content=body
    )
    click.echo(f"\nConstructed EmailContent:\n{email}")
    if not click.confirm("Proceed to action item entry?"):
        click.echo("Aborted.")
        return

    # Action item phase
    click.echo("\n== Action Item Entries ==")
    action_items = []
    while True:
        click.echo("\n-- New Action Item --")
        action_type_str = click.prompt(
            "Action Type", type=click.Choice([t.name for t in ActionType]))
        action_type = ActionType[action_type_str]
        description = click.prompt("Description")
        due_date_str = click.prompt(
            "Due Date (YYYY-MM-DD) or empty", default="", show_default=False)
        due_date = datetime.strptime(
            due_date_str, '%Y-%m-%d') if due_date_str else None
        confidence_score = click.prompt(
            "Confidence Score (0.0-1.0)", type=float, default=0.85)
        owners = []
        click.echo("Enter owner aliases (empty to finish):")
        while True:
            owner = click.prompt("Owner", default="", show_default=False)
            if not owner:
                break
            owners.append(Participant(alias=owner))
        waiters = []
        click.echo("Enter waiter aliases (empty to finish):")
        while True:
            waiter = click.prompt("Waiter", default="", show_default=False)
            if not waiter:
                break
            waiters.append(Participant(alias=waiter))
        metadata = {}
        action_item = ActionItem(
            action_type=action_type,
            description=description,
            confidence_score=confidence_score,
            message_id=message_id,
            due_date=due_date,
            owners=owners,
            waiters=waiters,
            metadata=metadata
        )
        action_items.append(action_item)
        click.echo(f"\nConstructed ActionItem:\n{action_item}")
        add_more = click.prompt("Add another action item? [y/N]", default="n")
        if add_more.lower() not in ("y", "yes"):
            break

    dataset = Dataset(file_path=dataset_path)
    for ai in action_items:
        dataset.append(DatasetLine(email=email, expected_action_items=[ai]))
    click.echo(f"{len(action_items)} entries added to {dataset.dataset_file}")
