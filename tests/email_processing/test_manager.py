from unittest import TestCase
from unittest.mock import MagicMock
from datetime import datetime

from matai.dao.sqlite.sqlite_dao import SQLiteActionItemDAO, SQLiteEmailContentDAO, SQLiteParticipantDAO
from matai.dao.interface import ActionItemDAO, EmailContentDAO

import sqlite3

from matai.manager.manager import EmailFilters, EmailManager
from matai.email_processing.model import EmailContent, EmailAddress, ActionItem, ActionType, Participant
from matai.manager.models import RunConfiguration 


def init_sqlite_db():
    connection = sqlite3.connect(':memory:')
    with open('./db/init_db_sqlite.sql', 'r') as f:
        connection.executescript(f.read())
    return connection


class EmailManagerTest(TestCase):

    def setUp(self):
        connection = init_sqlite_db()
        self._email_client = MagicMock()
        self._action_item_dao: ActionItemDAO = SQLiteActionItemDAO(connection)
        self._action_item_dao.delete_all_action_items()
        self._email_content_dao: EmailContentDAO = SQLiteEmailContentDAO(
            connection)
        self._participant_dao = SQLiteParticipantDAO(connection)
        self._processor = MagicMock()
        self.manager = EmailManager(
            self._email_client,
            self._action_item_dao,
            self._email_content_dao,
            self._processor,
            self._participant_dao)

        # Initialize a datetime object with the fixed date of 2024-01-01

        self._last_run_details = RunConfiguration(last_run_time=datetime(2024, 1, 1))

    def test_should_skip_already_stored_emails(self):
        # Given an email with id "001" returned by the email client
        #   And an email with id "001" retrieved by the store
        email = EmailContent(
            message_id="001",
            thread_id="thread-001",
            subject="Test Email",
            sender=EmailAddress.from_string("sender@example.com"),
            recipients=[EmailAddress.from_string("recipient@example.com")],
            raw_content="This is a test email.",
            timestamp=datetime.now()
        )

        self._email_client.read_messages.return_value = [
            email
        ]

        self._email_content_dao.create_email_content(email)

        # When managing the new emails
        actual = self.manager.process_new_emails(self._last_run_details)

        # Then no new emails are evaluated
        self.assertEqual(0, len(list(actual)))

    def test_should_process_new_emails(self):
        # Given an email with id "001" returned by the email client
        #   And no email retrieved by the store
        email = EmailContent(
            message_id="001",
            thread_id="thread-001",
            subject="Test Email",
            sender=EmailAddress.from_string("sender@example.com"),
            recipients=[EmailAddress.from_string("recipient@example.com")],
            raw_content="This is a test email.",
            timestamp=datetime.now()
        )

        action_1 = ActionItem(
            action_type=ActionType.DEADLINE,
            description="Complete the task",
            owners=[Participant(alias="Owner1", email=EmailAddress.from_string(
                "owner1@example.com"))],
            waiters=[],
            due_date=datetime.now(),
            confidence_score=0.9,
            message_id="001",
            metadata={}
        )
        action_2 = ActionItem(
            action_type=ActionType.TASK,
            description="Review the document",
            owners=[Participant(alias="Owner2", email=EmailAddress.from_string(
                "owner2@example.com"))],
            waiters=[],
            due_date=datetime.now(),
            confidence_score=0.85,
            message_id="001",
            metadata={}
        )
        self._email_client.read_messages.return_value = [
            email
        ]
        # When processing the emails
        self._processor.process_email.return_value = [
            action_1, action_2
        ]

        actual = self.manager.process_new_emails(self._last_run_details)

        # Then the email is returned along with the identified action items

        actual = list(actual)
        self.assertEqual(1, len(actual))
        self.assertEqual(email, actual[0][0])
        self.assertEqual(2, len(actual[0][1]))

    def test_should_ignore_emails_from_non_relevant_recipients_when_filters_are_set(self):
        # Given an email for the recipient mario.rossi@example.it
        #  And a filter requesting only emails for lucio.verdi@example.it

        to_be_filtered = EmailContent(
            message_id="001",
            thread_id="thread-001",
            subject="Test Email",
            sender=EmailAddress.from_string("sender@example.com"),
            recipients=[EmailAddress.from_string("mario.rossi@example.it")],
            raw_content="This is a test email.",
            timestamp=datetime.now()
        )

        wanted_email = EmailContent(
            message_id="002",
            thread_id="thread-002",
            subject="Test Email",
            sender=EmailAddress.from_string("sender@example.com"),
            recipients=[EmailAddress.from_string("lucio.verdi@example.it")],
            raw_content="This is a test email.",
            timestamp=datetime.now()
        )

        self._email_client.read_messages.return_value = [
            to_be_filtered, wanted_email
        ]

        action_1 = ActionItem(
            action_type=ActionType.TASK,
            description="Review the document",
            owners=[Participant(alias="Owner2", email=EmailAddress.from_string(
                "owner2@example.com"))],
            waiters=[],
            due_date=datetime.now(),
            confidence_score=0.85,
            message_id="001",
            metadata={}
        )
        self._processor.process_email.return_value = [
            action_1
        ]
        filters = EmailFilters(["lucio.verdi@example.it"])
        actual = self.manager.process_new_emails(
            self._last_run_details, filters)

        actual = list(actual)
        self.assertEqual(1, len(actual))
        self.assertEqual(wanted_email, actual[0][0])
