import json
from datetime import datetime
import pytest
from click.testing import CliRunner
from matai.benchmark.cli import cli
from matai.benchmark.dataset import Dataset, DatasetLine
from matai.email_processing.model import (
    EmailContent, ActionItem, EmailAddress, Participant, ActionType
)

@pytest.fixture
def tmp_dataset(tmp_path):
    p = tmp_path / "ds.jsonl"
    # start empty
    p.write_text("")
    return str(p)

def make_sample_entry():
    # build a minimal email+action
    email = EmailContent(
        message_id="m1",
        subject="Test",
        sender=EmailAddress.from_string("foo@bar.com"),
        recipients=[EmailAddress.from_string("baz@qux.com")],
        thread_id="t1",
        timestamp=datetime(2025,1,1,12,0,0),
        raw_content="hello"
    )
    ai = ActionItem(
        action_type=ActionType.TASK,
        description="desc",
        confidence_score=0.5,
        message_id="m1",
        due_date=None,
        owners=[Participant(alias="alice")],
        waiters=[],
        metadata={}
    )
    return DatasetLine(email=email, expected_action_items=[ai])

def test_show_empty(tmp_dataset):
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--dataset-path", tmp_dataset])
    assert result.exit_code == 0
    assert "No entries found." in result.output

def test_show_one_entry(tmp_dataset):
    # pre‐populate dataset
    ds = Dataset(file_path=tmp_dataset)
    ds.append(make_sample_entry())
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--dataset-path", tmp_dataset])
    assert result.exit_code == 0
    assert "Entry 1/1" in result.output
    assert "Subject: Test" in result.output
    assert "Action Item:" in result.output
    assert "Description: desc" in result.output

def test_add_abort(tmp_dataset, monkeypatch):
    # simulate user aborting at the first confirmation
    runner = CliRunner()
    # stub click.edit to return a body, stub confirm to return False
    monkeypatch.setattr("click.edit", lambda **kwargs: "body text")
    inputs = "\n".join([
        "m2",                   # message_id
        "Subj",                 # subject
        "foo@bar.com",          # sender
        "",                     # end recipients
        "thread-xyz",           # thread_id
        "",                     # timestamp (empty → now)
        "n",                    # Proceed to action item? → No
    ]) + "\n"
    result = runner.invoke(
        cli,
        ["add", "--dataset-path", tmp_dataset],
        input=inputs,
    )
    assert result.exit_code == 0
    assert "Aborted." in result.output
    # dataset still empty
    assert Dataset(file_path=tmp_dataset).load() == []
