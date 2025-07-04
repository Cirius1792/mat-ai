from datetime import datetime, timedelta
from behave import given, when, then  # type: ignore
from click.testing import CliRunner
from matai_v2.cli import cli
from unittest.mock import MagicMock
# Given steps


@given('the user is authenticated with the email provider')
def step_given_user_authenticated(context):
    context.auth_client.set_authenticated(True)


@given('no emails have been processed yet')
def step_given_no_emails_processed(context):
    pass


@given('no email retrieval timeframe is configured')
def step_given_no_timeframe_configured(context):
    pass


@given('there are emails from the last {days:d} days in the inbox')
def step_given_emails_from_last_days(context, days):
    email_date = datetime.now() - timedelta(days=days)
    for i in range(5):
        context.mock_outlook_client.add_message(message_id=1,
                                                subject=f"Test Email{i}",
                                                sender=f"sender{i}@company.com",
                                                body=f"Test email body {i}",
                                                timestamp=email_date,
                                                )


@given('some of these emails contain clear action items with due dates')
def step_given_emails_contain_action_items_with_due_dates(context):
    pass


@given('the email retrieval timeframe is configured to {days:d} days')
def step_given_email_timeframe_configured(context, days):
    context.email_retrieval_days = days


@given('some of these new emails contain clear action items with due dates')
def step_given_new_emails_contain_action_items_with_due_dates(context):
    pass


@given('some emails have been processed already')
def step_given_some_emails_processed_already(context):
    raise NotImplementedError('STEP: some emails have been processed already')


@given('there are new unprocessed emails in the inbox')
def step_given_new_unprocessed_emails(context):
    raise NotImplementedError(
        'STEP: there are new unprocessed emails in the inbox')


@given('there are new emails in the inbox')
def step_given_new_emails_in_inbox(context):
    raise NotImplementedError('STEP: there are new emails in the inbox')


@given('these emails contain no clear action items or deadlines')
def step_given_emails_contain_no_clear_action_items_or_deadlines(context):
    raise NotImplementedError(
        'STEP: these emails contain no clear action items or deadlines')


@given('some of these emails are spam or promotional content')
def step_given_emails_are_spam_or_promotional(context):
    raise NotImplementedError(
        'STEP: some of these emails are spam or promotional content')


@given('some emails contain clear action items')
def step_given_some_emails_contain_clear_action_items(context):
    raise NotImplementedError('STEP: some emails contain clear action items')


@given('some emails contain no actionable content')
def step_given_some_emails_contain_no_actionable_content(context):
    raise NotImplementedError(
        'STEP: some emails contain no actionable content')

# When steps


@when('I run the application with the "{command}" command')
def step_when_run_application(context, command):
    # Patch the email client's read_messages method so we can verify the call later
    context.app_context.email_client.read_messages = MagicMock(return_value=[])
    context.email_client_read_messages_mock = context.app_context.email_client.read_messages

    runner = CliRunner()
    context.result = runner.invoke(
        cli,
        [command],
        input="http://localhost:8080/?code=123",
        obj={"app_ctx": context.app_context},
    )

# Then steps


@then('the system should retrieve emails from the last {days:d} days')
def step_then_system_should_retrieve_emails_from_last_days(context, days):
    """Verify that read_messages was called with the expected start_date."""
    expected_start_date = datetime.now() - timedelta(days=days)

    mock = context.email_client_read_messages_mock
    assert mock.called, "Expected email_client.read_messages to be called"

    # Accept either start_date or start_days for backward-compatibility.
    called_kwargs = mock.call_args.kwargs
    start_date = called_kwargs.get("start_date") or called_kwargs.get("start_days")
    assert start_date is not None, "start_date argument not supplied to read_messages"

    # Allow a small timing difference (≤ 60 seconds)
    delta_seconds = abs((expected_start_date - start_date).total_seconds())
    assert (
        delta_seconds < 60
    ), f"start_date {start_date} differs from expected {expected_start_date} by more than 60 seconds"


@then('action items should be extracted from emails containing actionable content')
def step_then_action_items_extracted_from_emails_with_actionable_content(context):
    raise NotImplementedError(
        'STEP: action items should be extracted from emails containing actionable content')


@then('each extracted action item should have a non-empty description')
def step_then_each_extracted_action_item_should_have_non_empty_description(context):
    raise NotImplementedError(
        'STEP: each extracted action item should have a non-empty description')


@then('each extracted action item should have a non-empty due date')
def step_then_each_extracted_action_item_should_have_non_empty_due_date(context):
    raise NotImplementedError(
        'STEP: each extracted action item should have a non-empty due date')


@then('the action items should be stored in the local database')
def step_then_action_items_should_be_stored_in_database(context):
    raise NotImplementedError(
        'STEP: the action items should be stored in the local database')


@then('all processed emails should be marked as processed in the local database')
def step_then_all_processed_emails_marked_in_database(context):
    raise NotImplementedError(
        'STEP: all processed emails should be marked as processed in the local database')


@then('the system should only process emails not already marked as processed')
def step_then_system_only_process_unmarked_emails(context):
    raise NotImplementedError(
        'STEP: the system should only process emails not already marked as processed')


@then('action items should be extracted from the new emails containing actionable content')
def step_then_action_items_extracted_from_new_emails_with_actionable_content(context):
    raise NotImplementedError(
        'STEP: action items should be extracted from the new emails containing actionable content')


@then('the new action items should be stored in the local database')
def step_then_new_action_items_stored_in_database(context):
    raise NotImplementedError(
        'STEP: the new action items should be stored in the local database')


@then('the newly processed emails should be marked as processed in the local database')
def step_then_newly_processed_emails_marked_in_database(context):
    raise NotImplementedError(
        'STEP: the newly processed emails should be marked as processed in the local database')


@then('previously processed emails should remain unchanged')
def step_then_previously_processed_emails_remain_unchanged(context):
    raise NotImplementedError(
        'STEP: previously processed emails should remain unchanged')


@then('the system should process these emails')
def step_then_system_should_process_these_emails(context):
    raise NotImplementedError('STEP: the system should process these emails')


@then('no action items should be extracted from these emails')
def step_then_no_action_items_should_be_extracted_from_these_emails(context):
    raise NotImplementedError(
        'STEP: no action items should be extracted from these emails')


@then('these emails should be marked as processed in the local database')
def step_then_these_emails_should_be_marked_in_database(context):
    raise NotImplementedError(
        'STEP: these emails should be marked as processed in the local database')


@then('the system should continue processing other emails normally')
def step_then_system_should_continue_processing_other_emails_normally(context):
    raise NotImplementedError(
        'STEP: the system should continue processing other emails normally')


@then('no action items should be extracted from spam or promotional emails')
def step_then_no_action_items_should_be_extracted_from_spam_or_promotional_emails(context):
    raise NotImplementedError(
        'STEP: no action items should be extracted from spam or promotional emails')


@then('action items should only be extracted from emails with clear actionable content')
def step_then_action_items_should_only_be_extracted_from_emails_with_clear_actionable_content(context):
    raise NotImplementedError(
        'STEP: action items should only be extracted from emails with clear actionable content')


@then('all emails should be marked as processed in the local database')
def step_then_all_emails_should_be_marked_in_database(context):
    raise NotImplementedError(
        'STEP: all emails should be marked as processed in the local database')


@then('the extracted action items should have non-empty descriptions and due dates')
def step_then_extracted_action_items_should_have_non_empty_descriptions_and_due_dates(context):
    raise NotImplementedError(
        'STEP: the extracted action items should have non-empty descriptions and due dates')


@given(u'some emails are spam or promotional content')
def step_impl(context):
    raise NotImplementedError(
        u'STEP: some emails are spam or promotional content')
