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
    lines = []
    try:
        lines = dataset.load()
    except ValueError as e:
        click.echo(f"Error loading dataset: {e}")
        return 
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
    #TODO: check that there is not a line contaiing an email with the same unique_id
    # Email content phase
    click.echo("== Email Content Entry ==")
    message_id = click.prompt("Message ID (Optional)", default="", show_default=False)
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
    thread_id = click.prompt("Thread ID (Optional)", default="", show_default=False)
    if not thread_id:
        thread_id = str(uuid.uuid4())
    timestamp_str = click.prompt("Timestamp (YYYY-MM-DD HH:MM:SS or ISO) (Optional)", default="")
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

    if not click.confirm("Append entries?"):
        click.echo("Aborted.")
        return

    dataset = Dataset(file_path=dataset_path)
    dataset.append(DatasetLine(email=email, expected_action_items=action_items))
    click.echo(f"{len(action_items)} entries added to {dataset.dataset_file}")


@cli.command("edit")
@click.option("--dataset-path", type=click.Path(), default="dataset.jsonl",
              help="Path to the dataset file")
@click.option("--id", "email_id", required=True,
              help="Unique ID of the email content to edit")
def edit(dataset_path: str, email_id: str) -> None:
    """Edit an existing email entry and its action items in the dataset."""
    dataset = Dataset(file_path=dataset_path)
    lines = dataset.load()
    idxs = [i for i, dl in enumerate(lines) if dl.email.unique_id == email_id]
    if not idxs:
        click.echo(f"No entries found for ID: {email_id}")
        return
    assert len(idxs) == 1, "Multiple entries found for the same ID, which is unexpected."

    email = lines[idxs[0]].email
    click.echo("== Current Email Content ==")
    click.echo(str(email))
    click.echo("\n== Edit Email Content ==")
    subject = click.prompt("Subject", default=email.subject)
    sender_str = click.prompt("Sender", default=email.sender.to_string())
    sender = EmailAddress.from_string(sender_str)
    if click.confirm("Edit recipients?", default=False):
        recipients: list[EmailAddress] = []
        click.echo("Enter recipients (empty to finish):")
        while True:
            rec = click.prompt("Recipient", default="", show_default=False)
            if not rec:
                break
            recipients.append(EmailAddress.from_string(rec))
    else:
        recipients = email.recipients
    thread_id = click.prompt("Thread ID", default=email.thread_id,
                             show_default=False)
    timestamp_str = click.prompt(
        "Timestamp (YYYY-MM-DD HH:MM:SS or ISO)",
        default=email.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        show_default=False
    )
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.fromisoformat(timestamp_str)
    if click.confirm("Edit body?", default=False):
        new_body = click.edit(text=email.raw_content) or email.raw_content
    else:
        new_body = email.raw_content

    # Update the email content in the dataset line
    e = lines[idxs[0]].email
    e.subject = subject
    e.sender = sender
    e.recipients = recipients
    e.thread_id = thread_id
    e.timestamp = timestamp
    e.raw_content = new_body
    e._body = new_body
    e._clean_body = None

    click.echo("\n== Edit Action Items ==")
    all_ai = [ai for i in idxs for ai in lines[i].expected_action_items]
    while True:
        choice = click.prompt(
            "Choose action", type=click.Choice(["add", "edit", "done"]),
            default="done"
        )
        if choice == "add":
            click.echo("\n-- New Action Item --")
            action_type_str = click.prompt(
                "Action Type",
                type=click.Choice([t.name for t in ActionType])
            )
            action_type = ActionType[action_type_str]
            description = click.prompt("Description")
            due_date_str = click.prompt(
                "Due Date (YYYY-MM-DD) or empty", default="",
                show_default=False
            )
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
            confidence_score = click.prompt(
                "Confidence Score (0.0-1.0)", type=float, default=0.85
            )
            owners: list[Participant] = []
            click.echo("Enter owner aliases (empty to finish):")
            while True:
                owner = click.prompt("Owner", default="", show_default=False)
                if not owner:
                    break
                owners.append(Participant(alias=owner))
            waiters: list[Participant] = []
            click.echo("Enter waiter aliases (empty to finish):")
            while True:
                waiter = click.prompt("Waiter", default="", show_default=False)
                if not waiter:
                    break
                waiters.append(Participant(alias=waiter))
            metadata: dict[str, str] = {}
            new_ai = ActionItem(
                action_type=action_type,
                description=description,
                confidence_score=confidence_score,
                message_id=email_id,
                due_date=due_date,
                owners=owners,
                waiters=waiters,
                metadata=metadata
            )
            lines.append(DatasetLine(email=lines[idxs[0]].email,
                                     expected_action_items=[new_ai]))
            all_ai.append(new_ai)
            click.echo(f"\nConstructed ActionItem:\n{new_ai}")
        elif choice == "edit":
            if not all_ai:
                click.echo("No action items to edit.")
                continue
            click.echo("\n-- Edit Existing Action Item --")
            for num, ai in enumerate(all_ai, start=1):
                click.echo(f"{num}) {ai.description}")
            idx_choice = click.prompt("Select action item to edit", type=int)
            if not (1 <= idx_choice <= len(all_ai)):
                click.echo("Invalid selection.")
                continue
            ai = all_ai[idx_choice-1]
            atype = click.prompt(
                "Action Type",
                type=click.Choice([t.name for t in ActionType]),
                default=ai.action_type.name
            )
            ai.action_type = ActionType[atype]
            ai.description = click.prompt("Description", default=ai.description)
            due_str = click.prompt(
                "Due Date (YYYY-MM-DD) or empty", default=
                (ai.due_date.strftime('%Y-%m-%d') if ai.due_date else ""),
                show_default=False
            )
            ai.due_date = datetime.strptime(due_str, '%Y-%m-%d') if due_str else None
            ai.confidence_score = click.prompt(
                "Confidence Score (0.0-1.0)", type=float,
                default=ai.confidence_score
            )
            if click.confirm("Edit owners?", default=False):
                new_owners: list[Participant] = []
                click.echo("Enter owner aliases (empty to finish):")
                while True:
                    owner = click.prompt("Owner", default="", show_default=False)
                    if not owner:
                        break
                    new_owners.append(Participant(alias=owner))
                ai.owners = new_owners
            if click.confirm("Edit waiters?", default=False):
                new_waiters: list[Participant] = []
                click.echo("Enter waiter aliases (empty to finish):")
                while True:
                    waiter = click.prompt("Waiter", default="", show_default=False)
                    if not waiter:
                        break
                    new_waiters.append(Participant(alias=waiter))
                ai.waiters = new_waiters
        else:
            break

    if not click.confirm("Save changes?", default=True):
        click.echo("Aborted.")
        return

    dataset.save(lines)
    click.echo(f"Dataset updated with {len(lines)} entries at {dataset.dataset_file}")
