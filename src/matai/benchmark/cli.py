import click
from matai.benchmark.dataset import Dataset, DatasetLine
from matai.email_processing.model import EmailContent, ActionItem, EmailAddress, Participant, ActionType
from datetime import datetime

@click.group()
def cli():
    """CLI to manage the benchmark dataset."""
    pass
# Add a command show to print all the entries in the dataset in a human readable format. If the entries fill more than the space available in the terminal, implement pagination. to exit the paginated view the user will press the 'q' key. AI!

@cli.command("add")
@click.option("--dataset-path", type=click.Path(), default="dataset.jsonl", help="Path to the dataset file")
def add(dataset_path):
    """Add a new entry to the dataset."""
    # Email content phase
    click.echo("== Email Content Entry ==")
    message_id = click.prompt("Message ID")
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
    thread_id = click.prompt("Thread ID", default="")
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
    click.echo("\n== Action Item Entry ==")
    action_type_str = click.prompt("Action Type", type=click.Choice([t.name for t in ActionType]))
    action_type = ActionType[action_type_str]
    description = click.prompt("Description")
    due_date_str = click.prompt("Due Date (YYYY-MM-DD) or empty", default="", show_default=False)
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
    confidence_score = click.prompt("Confidence Score (0.0-1.0)", type=float, default=0.85)
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
    click.echo(f"\nConstructed ActionItem:\n{action_item}")
    if not click.confirm("Append to dataset?"):
        click.echo("Aborted.")
        return

    dataset = Dataset(file_path=dataset_path)
    dataset.append(DatasetLine(email=email, expected_action_item=action_item))
    click.echo(f"Entry added to {dataset.dataset_file}")
