import logging
import os
from pathlib import Path
from typing import Optional
import yaml
from nicegui import ui

from configuration import Config, DatabaseConfig, FiltersConfig, LLMConfig, OutlookConfig, TrelloConfig
from configuration.application_configuration import ApplicationContext
from matai.common.logging import configure_logging
from matai.integrations.trello import TrelloClient

log_file = os.getenv("LOG_FILE", "./logs/pmai.log")
configure_logging(log_file=Path(log_file))
logger = logging.getLogger(__name__)

# Try to load existing config or create new one
configuration_path = os.getenv('PMAI_CONFIG_PATH', 'config/config.yaml')
try:
    config = Config.load_config_from_yaml(configuration_path)
    logger.info("Loaded config from file: %s", config)
except FileNotFoundError:
    logger.info("No existing config found, creating new one")
    config = Config(DatabaseConfig(), {"outlook": OutlookConfig("Outlook")}, {
        "trello": TrelloConfig("Trello")}, FiltersConfig(), LLMConfig(host="", api_key=""))
except yaml.YAMLError as e:
    logger.error("Failed to parse config file: %s", e)
    raise SystemExit("Cannot continue with invalid configuration file")


if not config.llm_config.api_key:
    env_api_key = os.getenv("OPENAI_API_KEY")
    if env_api_key:
        config.llm_config.api_key = env_api_key


def create_card(content_function):
    with ui.card().style('width: 400px;'):
        content_function()


def header(title: str):
    ui.label(title).classes('text-lg font-bold')


def create_input_field(label, obj, attribute_name: str):
    return ui.input(label).bind_value(obj, attribute_name).style('width: 100%;')


def create_slider_field(min_val, max_val, step, obj, attribute_name: str):
    """Creates a slider input field with a label showing the current value.

    Args:
        min_val: Minimum value for the slider
        max_val: Maximum value for the slider
        step: Step size for slider increments
        obj: Object instance to bind the value to
        attribute_name: Name of the attribute on obj to bind to

    Returns:
        A column containing the slider and its value label
    """
    with ui.column().style('width: 100%;'):
        slider = ui.slider(min=min_val, max=max_val, step=step).bind_value(
            obj, attribute_name).style('width: 100%;')
        ui.label().bind_text_from(slider, 'value')


def outlook_config_card_content():
    header('Outlook Configuration')
    create_input_field('Client id', config.email['outlook'], "client_id")
    create_input_field('Secret', config.email['outlook'], "client_secret")
    create_input_field('Tenant id', config.email['outlook'], "tenant_id")

    def show_auth_modal():
        app_context = init_application()
        if not app_context:
            ui.notify("Please save configuration first", color="negative")
            return
        if app_context.outlook_auth_client.is_authenticated:
            ui.notify("Already authenticated", color="positive")
            return

        with ui.dialog() as auth_dialog, ui.card():
            ui.label("O365 Authentication").classes('text-lg font-bold')

            # Get authentication link
            try:
                auth_link, flow = app_context.outlook_auth_client.get_auth_link()
                ui.label("Please visit this URL to authenticate:").classes('mt-4')
                ui.label(auth_link).classes('break-all text-primary')

                # Create token input field
                token_input = ui.input(
                    "Paste authentication URL here").classes('w-full mt-4')
                error_message = ui.label("").classes('text-red-500 hidden')

                def complete_auth():
                    # Try to complete authentication with the token URL
                    result = app_context.outlook_auth_client.complete_authentication(
                        token_input.value)
                    if result:
                        auth_dialog.close()
                        ui.notify(
                            "Authentication completed successfully", color="positive")
                    else:
                        error_message.text = "Authentication failed. Please try again."
                        error_message.classes('text-red-500')

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button("Cancel", on_click=auth_dialog.close).classes(
                        'mr-2')
                    ui.button("Authenticate", on_click=complete_auth).classes(
                        'bg-primary')

            except Exception as e:
                logger.error("Authentication error: %s", e)
                ui.label(f"Error: {str(e)}").classes('text-red-500')
                ui.button("Close", on_click=auth_dialog.close)

        auth_dialog.open()

    ui.button("Start Authentication", on_click=show_auth_modal).classes('mt-2')


def trello_config_card_content():
    # API Configuration Section
    with ui.column().classes('w-full'):
        header('Trello API Configuration')

        def update_board_selection():
            # Clear previous content
            board_container.clear()

            assert config.board['trello'], "Trello config is not set"
            assert isinstance(config.board['trello'], TrelloConfig)

            if config.board['trello'].api_key and config.board['trello'].api_token:
                try:
                    client = TrelloClient(
                        config.board['trello'].api_key, config.board['trello'].api_token)
                    boards = client.boards()
                    logger.debug("Boards fetched: %s", [
                                 board.name for board in boards])

                    with board_container:
                        ui.label('Which board do you want to use?')
                        ui.select(
                            options={board.id: board.name for board in boards},
                            label='Select Board'
                        ).bind_value(config.board['trello'], "board").style('width: 100%;')
                except Exception as e:
                    logger.error(f"Failed to fetch Trello boards: {e}")
                    with board_container:
                        ui.label(f'Error fetching boards: {str(e)}').classes(
                            'text-red-500')

        # Create input fields that trigger board selection update
        api_key_input = create_input_field(
            'API Key', config.board['trello'], "api_key")
        api_token_input = create_input_field(
            'API Token', config.board['trello'], "api_token")

        # Create container for board selection that we can update
        board_container = ui.row().classes('w-full items-center')

        # Update board selection when either field changes
        api_key_input.on('change', update_board_selection)
        api_token_input.on('change', update_board_selection)
        update_board_selection()


def filters_config_card_content():
    header('Filters Configuration')
    ui.label("Confidence Level")
    create_slider_field(0, 1, 0.05, config, "confidence_level")

    # Recipients section
    ui.label('Recipients').classes('mt-4')
    recipients_container = ui.row().classes('gap-2 flex-wrap')

    def add_recipient(email: str, update_config=True):
        """Add a recipient chip to the UI and optionally update config

        Args:
            email: Email address to add
            update_config: Whether to update the config object (False when loading existing)
        """
        if email and (update_config or email in config.filters.recipients):
            if update_config and email not in config.filters.recipients:
                config.filters.recipients.append(email)
            with recipients_container:
                chip = ui.chip(
                    text=email,
                    icon='mail',
                    removable=True,
                    color='primary',
                )
                chip.on("remove", lambda: config.filters.recipients.remove(email))

    email_input = ui.input(
        label='Add recipient email',
        placeholder='Enter email and press Enter',
        validation={'Invalid email': lambda value: not value or '@' in value}
    ).style('width: 100%;')

    email_input.on('keydown.enter', lambda e: (
        add_recipient(email_input.value, update_config=True),
        email_input.set_value('')
    ))

    # Add existing recipients as chips
    for email in config.filters.recipients:
        add_recipient(email, update_config=False)


def init_application() -> Optional[ApplicationContext]:
    try:
        return ApplicationContext.init(config)
    except Exception as e:
        logger.error("Failed to initialize application context: %s", e)

    return None


def llm_provider_config_card_content():
    header('LLM Provider Configuration')

    # Create dropdown for LLM provider selection with options "open AI" and "other"
    provider_select = ui.select(
        options={"open AI": "Open AI", "other": "other"},
        label="LLM Provider"
    ).style("width: 100%;")

    # Bind the select value to llm_config.provider
    provider_select.bind_value(config.llm_config, "provider")

    # Set default selection if not already set
    if not config.llm_config.provider and "OPENAI_API_KEY" in os.environ:
        config.llm_config.provider = "Open AI"
        config.llm_config.api_key = os.environ["OPENAI_API_KEY"]

    provider_select.value = config.llm_config.provider
    print(f"Provider selected: {provider_select.value}")

    # Create a container for the input fields first.
    with ui.column().classes('w-full') as fields_container:
        def update_fields():
            fields_container.clear()
            # If "Open AI" is selected, show only the API key input.
            if provider_select.value == "Open AI":
                create_input_field('API Key', config.llm_config, "api_key")
            else:
                # If "other" is selected, show both Host and API key inputs.
                create_input_field('Host', config.llm_config, "host")
                create_input_field('API Key', config.llm_config, "api_key")
            create_input_field('Model', config.llm_config, "model")

        provider_select.on("change", update_fields)
        update_fields()

def database_config_card_content():
    header('Database Configuration')
    create_input_field('Database Name', config.database, "name")
    create_input_field('User', config.database, "user")
    create_input_field('Password', config.database, "password")
    create_input_field('Host', config.database, "host")
    create_input_field('Port', config.database, "port")

# Create status indicator


def update_status(status_label, execute_button):
    """Update the status indicator based on ApplicationContext initialization"""
    ctx = init_application()
    if ctx is not None and ctx.outlook_auth_client.is_authenticated:
        status_label.classes('text-green-500 text-2xl')
        execute_button.enable()
    else:
        status_label.classes('text-red-500 text-2xl')
        execute_button.disable()


def process_new_emails():
    from matai.commands.process_new_emails_command import ProcessNewEmailsCommand
    # Instantiate the dependencies for ProcessNewEmailsCommand.
    # Replace the None values with actual instances as needed.
    ctx: Optional[ApplicationContext] = init_application()
    assert ctx is not None, "Failed to initialize application context"
    try:
        with ui.dialog() as process_dialog:
            ui.spinner(size="lg").style(
                'width: 100%; height: 100%;')
            command = ProcessNewEmailsCommand(ctx.run_configuration_dao,
                                              ctx.email_manager,
                                              ctx.configuration.filters,
                                              ctx.integration_manager,
                                              ctx.execution_report_dao)
            command.execute()
    except Exception:
        logger.exception("Failed to process emails")
        ui.notify("Failed to process emails", color="negative")
        return


# ======================================
# Create the actual configuration page
# ======================================
with ui.column().style('display: flex; flex-direction: column; justify-content: flex-start; align-items: center; min-height: 100vh; width: 100vw; overflow-y: auto;'):
    # Add status indicator at the top
    with ui.card().style('width: 400px;'):
        with ui.row():
            ui.label('Status:').classes('text-lg font-bold')
            status_label = ui.label('●')
            process_enabled = True if init_application() is not None else False
            execute_button = ui.button(
                "Process New Emails", on_click=process_new_emails)
            update_status(status_label, execute_button)
    create_card(outlook_config_card_content)
    create_card(trello_config_card_content)
    create_card(filters_config_card_content)
    create_card(llm_provider_config_card_content)
    create_card(database_config_card_content)

    def save_config():
        """Save configuration and update status"""
        try:
            Config.save_config_to_yaml(config, configuration_path)
            update_status(status_label, execute_button)
            ui.notify("Configuration saved successfully", color="positive")
        except:
            ui.notify("Failed to save configuration", color="negative")
            return

    ui.button('Save', on_click=save_config)


def _start_gui():
    pass


ui.run()
