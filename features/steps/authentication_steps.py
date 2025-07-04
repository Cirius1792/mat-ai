from behave import given, when, then  # type: ignore
import os
import yaml
from click.testing import CliRunner
from matai_v2.cli import cli
from matai_v2.email import O365Account
from matai_v2.context import ApplicationContext
from matai_v2.configuration import load_config_from_yaml

CONFIG_PATH = "config.yaml"

class MockO365Account(O365Account):
    def __init__(self, credentials, tenant_id, **kwargs):
        self._is_authenticated = False
        self.auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..."
        self.flow = None

    def get_auth_link(self):
        return self.auth_url, self.flow

    def complete_authentication(self, token_url, **kwargs):
        if "123" in token_url:
            self._is_authenticated = True
            return True
        return False

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def set_authenticated(self, value: bool):
        self._is_authenticated = value

def create_config_file_with_outlook(tenant_id, client_id, client_secret, redirect_uri):
    config = {
        "outlook_config": {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
    }
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f)

@given("a valid configuration file exists with Outlook settings")
def step_given_valid_config(context):
    create_config_file_with_outlook(
        tenant_id="test_tenant_id",
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8080",
    )
    os.environ['PMAI_CONFIG_PATH'] = CONFIG_PATH
    context.auth_client = MockO365Account(
        ("test_client_id", "test_client_secret"), "test_tenant_id"
    )
    config = load_config_from_yaml(CONFIG_PATH)
    context.app_context = ApplicationContext.init(config, auth_client=context.auth_client)

@given("the application is not authenticated")
def step_given_not_authenticated(context):
    context.auth_client.set_authenticated(False)

@when('I run the "authenticate" command')
def step_when_run_authenticate(context):
    runner = CliRunner()
    context.result = runner.invoke(cli, ["authenticate"], input="http://localhost:8080/?code=123", obj={
        "app_ctx": context.app_context
    })

@then('I should see "Please visit this URL to authenticate:"')
def step_then_see_auth_url(context):
    assert "Please visit this URL to authenticate:" in context.result.output

@then("I should be prompted to paste the URL")
def step_then_see_prompt(context):
    assert "Authentication URL:" in context.result.output

@then('I should see "Authentication completed successfully"')
def step_then_see_success(context):
    assert "Authentication completed successfully" in context.result.output

@given("the application is already authenticated")
def step_given_authenticated(context):
    context.auth_client.set_authenticated(True)

@then('I should see "Already authenticated"')
def step_then_see_already_authenticated(context):
    assert "Already authenticated" in context.result.output
