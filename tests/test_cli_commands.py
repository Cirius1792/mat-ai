import os
import yaml
import pytest
from click.testing import CliRunner

from configuration import Config, FiltersConfig, LLMConfig, OutlookConfig, TrelloConfig, DatabaseConfig
from matai.email_processing.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def default_config(tmp_path, monkeypatch):
    """Provide a minimal valid config file and set PMAI_CONFIG_PATH."""
    config = Config(
        database=DatabaseConfig(name="sqlite", host="", user="", password="", port=0),
        email={"outlook": OutlookConfig(name="outlook", tenant_id="", client_id="", client_secret="", redirect_uri="")},
        board={"trello": TrelloConfig(name="trello", api_key="", api_token="", board="")},
        filters=FiltersConfig(recipients=[]),
        llm_config=LLMConfig(host="", model="", api_key="", provider=""),
        confidence_level=0.5,
    )
    config_path = tmp_path / "config.yaml"
    Config.save_config_to_yaml(config, str(config_path))
    monkeypatch.setenv("PMAI_CONFIG_PATH", str(config_path))
    return config


@pytest.fixture(autouse=True)
def stub_context(monkeypatch):
    """Stub ApplicationContext.init and ProcessNewEmailsCommand to isolate CLI behavior."""
    import matai.email_processing.cli as cli_mod

    # Dummy authentication client
    class DummyAuthClient:
        def __init__(self):
            self.is_authenticated = False

        def get_auth_link(self):
            # Return link and a dummy flow as a tuple (unused by CLI)
            return "http://auth.url", None

        def complete_authentication(self, url):
            return url == "http://redirected"

    # Dummy DAO with no data
    class DummyDAO:
        def list_action_items(self):
            return []

        def list_email_contents(self):
            return []

        def get_email_content(self, _):
            return None

        def retrieve_last(self, _):
            return []

    # Build dummy context
    dummy_ctx = type("Ctx", (), {
        "action_item_dao": DummyDAO(),
        "email_content_dao": DummyDAO(),
        "execution_report_dao": DummyDAO(),
        "outlook_auth_client": DummyAuthClient(),
        "run_configuration_dao": None,
        "email_manager": None,
        "integration_manager": None,
    })()

    # Patch ApplicationContext.init to return dummy context
    monkeypatch.setattr(cli_mod.ApplicationContext, "init", staticmethod(lambda config: dummy_ctx))
    # Patch ProcessNewEmailsCommand to a no-op
    class DummyProcess:
        def __init__(self, *args, **kwargs):
            self.executed = False

        def execute(self):
            self.executed = True

    monkeypatch.setattr(cli_mod, "ProcessNewEmailsCommand", DummyProcess)
    return dummy_ctx


def test_list_action_items_empty(runner):
    result = runner.invoke(cli, ["list-action-items"])
    assert result.exit_code == 0
    assert "No pending action items." in result.output


def test_list_emails_empty(runner):
    result = runner.invoke(cli, ["list-emails"])
    assert result.exit_code == 0
    assert "No emails stored." in result.output


def test_show_email_not_found(runner):
    result = runner.invoke(cli, ["show-email", "123"])
    assert result.exit_code == 0
    assert "No email found with Message ID: 123" in result.output


def test_run_history_empty(runner):
    result = runner.invoke(cli, ["run-history", "3"])
    assert result.exit_code == 0
    assert "No execution reports found." in result.output


def test_authenticate_flow(monkeypatch, runner, stub_context):
    # Simulate input of redirect URL that completes authentication
    monkeypatch.setattr("builtins.input", lambda prompt="": "http://redirected")
    result = runner.invoke(cli, ["authenticate"])
    assert result.exit_code == 0
    assert "Please visit this URL to authenticate:" in result.output
    assert "http://auth.url" in result.output
    assert "Authentication completed successfully" in result.output


def test_authenticate_already_authenticated(runner, stub_context):
    stub_context.outlook_auth_client.is_authenticated = True
    result = runner.invoke(cli, ["authenticate"])
    assert result.exit_code == 0
    assert "Already authenticated" in result.output


def test_run_requires_authentication(runner):
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0
    assert "Please authenticate first." in result.output


def test_run_executes_command(runner, stub_context):
    stub_context.outlook_auth_client.is_authenticated = True
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0
    assert "New emails processed successfully." in result.output


def test_config_no_verify(runner):
    result = runner.invoke(cli, ["config"])
    assert result.exit_code == 0
    assert "Please specify a configuration file to verify with --verify" in result.output


def test_config_verify_missing(runner, tmp_path):
    missing = tmp_path / "nofile.yaml"
    result = runner.invoke(cli, ["config", "--verify", str(missing)])
    # click.Path(exists=True) causes a usage error when file is missing
    assert result.exit_code == 2
    assert "Invalid value for '--verify'" in result.output


def test_config_verify_invalid(runner, tmp_path):
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("::: not yaml :::")
    result = runner.invoke(cli, ["config", "--verify", str(invalid)])
    assert result.exit_code == 0
    assert "Error: Invalid YAML format in configuration file" in result.output


def test_config_verify_success(runner, tmp_path):
    config = Config(
        database=DatabaseConfig(name="sqlite", host="", user="", password="", port=0),
        email={"outlook": OutlookConfig(name="outlook", tenant_id="", client_id="", client_secret="", redirect_uri="")},
        board={"trello": TrelloConfig(name="trello", api_key="", api_token="", board="")},
        filters=FiltersConfig(recipients=[]),
        llm_config=LLMConfig(host="", model="", api_key="", provider=""),
        confidence_level=0.5,
    )
    good = tmp_path / "good.yaml"
    Config.save_config_to_yaml(config, str(good))
    result = runner.invoke(cli, ["config", "--verify", str(good)])
    assert result.exit_code == 0
    assert "Configuration file is valid. Parsed configuration:" in result.output
    assert "confidence_level" in result.output