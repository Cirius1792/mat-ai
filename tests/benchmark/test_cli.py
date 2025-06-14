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

@pytest.mark.timeout(2)
def test_show_empty(tmp_dataset):
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "--dataset-path", tmp_dataset])
    assert result.exit_code == 0
    assert "No entries found." in result.output

@pytest.mark.timeout(2)
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

@pytest.mark.timeout(2)
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

@pytest.mark.timeout(2)
def test_add_success(tmp_dataset, monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("click.edit", lambda **kwargs: "email body")
    monkeypatch.setattr("click.confirm", lambda prompt=True: True)
    inputs = "\n".join([
        "m3",                        # message_id
        "Subj2",                     # subject
        "foo2@bar.com",              # sender
        "",                          # end recipients
        "thread-2",                  # thread_id
        "2025-06-11 10:00:00",       # timestamp
        # entering action items
        "TASK",                      # action type
        "Do something",              # description
        "",                          # due_date empty
        "0.9",                       # confidence
        "alice",                     # owner
        "",                          # end owners
        "",                          # end waiters

        "y",                         # add one more action items

        # entering action items
        "TASK",                      # action type
        "Do something else",              # description
        "",                          # due_date empty
        "0.9",                       # confidence
        "alice",                     # owner
        "",                          # end owners
        "",                          # end waiters

        "n",                         # no more action items
        "y"                          # confirm append
    ]) + "\n"
    result = runner.invoke(cli, ["add", "--dataset-path", tmp_dataset], input=inputs)
    assert result.exit_code == 0
    ds_lines = Dataset(file_path=tmp_dataset).load()
    assert len(ds_lines) == 1
    dl = ds_lines[0]
    assert dl.email.message_id == "m3"
    assert dl.email.body == "email body"
    ai = dl.expected_action_items[0]
    assert ai.action_type == ActionType.TASK
    assert ai.description == "Do something"
    assert ai.confidence_score == 0.9


@pytest.mark.timeout(2)
def test_edit_nonexistent(tmp_dataset):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["edit", "--dataset-path", tmp_dataset, "--id", "noexist"]
    )
    assert result.exit_code == 0
    assert "No entries found for ID: noexist" in result.output


@pytest.mark.timeout(2)
def test_edit_abort(tmp_dataset, monkeypatch):
    ds = Dataset(file_path=tmp_dataset)
    ds.append(make_sample_entry())
    runner = CliRunner()
    def fake_confirm(prompt=None, default=False):
        if prompt and "Save changes" in prompt:
            return False
        return False
    monkeypatch.setattr("click.confirm", fake_confirm)
    monkeypatch.setattr("click.edit", lambda text=None: "edited body")
    inputs = "\n".join(["", "", "", "", ""]) + "\n"
    result = runner.invoke(
        cli,
        ["edit", "--dataset-path", tmp_dataset, "--id", "m1_t1"],
        input=inputs,
    )
    assert result.exit_code == 0
    assert "Aborted." in result.output
    lines = Dataset(file_path=tmp_dataset).load()
    assert len(lines) == 1
    assert lines[0].email.raw_content == "hello"


@pytest.mark.timeout(2)
def test_edit_update_subject(tmp_dataset, monkeypatch):
    ds = Dataset(file_path=tmp_dataset)
    ds.append(make_sample_entry())
    runner = CliRunner()
    def fake_confirm(prompt=None, default=False):
        if prompt and "Edit recipients" in prompt:
            return False
        if prompt and "Edit body" in prompt:
            return False
        if prompt and "Save changes" in prompt:
            return True
        return False
    monkeypatch.setattr("click.confirm", fake_confirm)
    monkeypatch.setattr("click.edit", lambda text=None: "irrelevant")
    inputs = "\n".join([
        "New Subject",
        "",
        "",
        "",
        "",
    ]) + "\n"
    result = runner.invoke(
        cli,
        ["edit", "--dataset-path", tmp_dataset, "--id", "m1_t1"],
        input=inputs,
    )
    assert result.exit_code == 0
    lines = Dataset(file_path=tmp_dataset).load()
    assert lines[0].email.subject == "New Subject"


@pytest.mark.timeout(2)
def test_edit_add_action_item(tmp_dataset, monkeypatch):
    ds = Dataset(file_path=tmp_dataset)
    ds.append(make_sample_entry())
    runner = CliRunner()
    def fake_confirm(prompt=None, default=False):
        if prompt and "Edit recipients" in prompt:
            return False
        if prompt and "Edit body" in prompt:
            return False
        if prompt and "Save changes" in prompt:
            return True
        return False
    monkeypatch.setattr("click.confirm", fake_confirm)
    monkeypatch.setattr("click.edit", lambda text=None: "")
    inputs = "\n".join([
        "",
        "",
        "",
        "",
        "add",
        "TASK",
        "extra",
        "",
        "0.7",
        "bob",
        "",
        "",
    ]) + "\n"
    result = runner.invoke(
        cli,
        ["edit", "--dataset-path", tmp_dataset, "--id", "m1_t1"],
        input=inputs,
    )
    assert result.exit_code == 0
    lines = Dataset(file_path=tmp_dataset).load()
    assert len(lines) == 2
    descs = [ai.description for dl in lines for ai in dl.expected_action_items]
    assert "extra" in descs


@pytest.mark.timeout(2)
def test_edit_modify_action_item(tmp_dataset, monkeypatch):
    ds = Dataset(file_path=tmp_dataset)
    ds.append(make_sample_entry())
    runner = CliRunner()
    def fake_confirm(prompt=None, default=False):
        if prompt and "Edit recipients" in prompt:
            return False
        if prompt and "Edit body" in prompt:
            return False
        if prompt and "Edit owners" in prompt:
            return False
        if prompt and "Edit waiters" in prompt:
            return False
        if prompt and "Save changes" in prompt:
            return True
        return False
    monkeypatch.setattr("click.confirm", fake_confirm)
    monkeypatch.setattr("click.edit", lambda text=None: "")
    inputs = "\n".join([
        "",
        "",
        "",
        "",
        "edit",
        "1",
        "TASK",
        "newdesc",
        "",
        "0.8",
        "",
    ]) + "\n"
    result = runner.invoke(
        cli,
        ["edit", "--dataset-path", tmp_dataset, "--id", "m1_t1"],
        input=inputs,
    )
    assert result.exit_code == 0
    lines = Dataset(file_path=tmp_dataset).load()
    assert lines[0].expected_action_items[0].description == "newdesc"
