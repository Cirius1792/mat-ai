import unittest
import sqlite3
import os
from datetime import datetime
from matai.dao.sqlite.sqlite_dao import SQLiteActionItemDAO, SQLiteEmailContentDAO
from matai.email_processing.model import ActionItem, EmailAddress, EmailContent, ActionType, Participant


class TestDAOIntegration(unittest.TestCase):
    """
    Integration test for DAOs using a real SQLite DB defined by init_db.sql.
    Ensure that each DAO method behaves as expected whenever we create,
    read, update, or delete records.
    """

    @classmethod
    def setUpClass(cls):
        """Set up a temporary SQLite DB using init_db.sql once for all tests."""
        cls.db_path = "test_integration.db"
        # If a leftover DB file exists, remove it
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        # Initialize it with init_db.sql
        cls.connection = sqlite3.connect(cls.db_path)
        with open("./db/init_db_sqlite.sql", "r") as f:
            cls.connection.executescript(f.read())
        cls.connection.commit()

    def setUp(self):
        """Create fresh DB connection for each test & instantiate DAOs."""
        self.connection = sqlite3.connect(self.__class__.db_path)
        self.action_item_dao = SQLiteActionItemDAO(self.connection)
        self.email_content_dao = SQLiteEmailContentDAO(self.connection)

    def tearDown(self):
        """Close DB connection after each test."""
        self.connection.close()

    @classmethod
    def tearDownClass(cls):
        """Remove the test DB file after all tests are done."""
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_action_item_crud(self):
        """Test creation, retrieval, update, and deletion of an action item."""
        # create
        item = ActionItem(
            action_type=ActionType.DEADLINE,
            description="Complete integration test",
            owners=[Participant(alias="Test User1")],
            waiters=[Participant(alias="Test User2")],
            due_date=datetime.now(),
            confidence_score=0.95,
            message_id="001",
            metadata={}
        )
        self.action_item_dao.create_action_item(item)
        item_id = item.id

        # retrieve
        retrieved = self.action_item_dao.get_action_item(item_id)
        assert retrieved is not None
        self.assertIsNotNone(retrieved, "Retrieved action_item should not be None.")
        self.assertEqual(retrieved.id, item_id)
        self.assertEqual(retrieved.description, "Complete integration test")
        self.assertEqual(retrieved.message_id, "001")

        # update
        item.description = "Updated integration test detail"
        self.action_item_dao.update_action_item(item)
        updated = self.action_item_dao.get_action_item(item_id)
        assert updated is not None
        self.assertEqual(updated.description, "Updated integration test detail")

        # delete
        self.action_item_dao.delete_action_item(item_id)
        deleted = self.action_item_dao.get_action_item(item_id)
        self.assertIsNone(deleted, "ActionItem should be None after deletion.")

    def test_email_content_crud(self):
        """Test creation, retrieval, update, and deletion of email content."""
        # create
        email = EmailContent(
            message_id="email-123",
            thread_id="thread-123",
            subject="Hello from the test",
            sender=EmailAddress.from_string("sender@example.com"),
            recipients=[EmailAddress.from_string("recipient@example.com")],
            raw_content="Test Body",
            timestamp=datetime.now()
        )
        self.email_content_dao.create_email_content(email)

        # retrieve
        retrieved_email = self.email_content_dao.get_email_content("email-123")
        assert retrieved_email is not None
        self.assertIsNotNone(retrieved_email, "Retrieved email_content should not be None.")
        self.assertEqual(retrieved_email.subject, "Hello from the test")

        # update
        email.subject = "Updated Subject"
        self.email_content_dao.update_email_content(email)
        updated_email = self.email_content_dao.get_email_content("email-123")
        assert updated_email is not None
        self.assertEqual(updated_email.subject, "Updated Subject")

        # delete
        self.email_content_dao.delete_email_content("email-123")
        should_be_none = self.email_content_dao.get_email_content("email-123")
        self.assertIsNone(should_be_none, "EmailContent should be None after deletion.")


if __name__ == "__main__":
    unittest.main()
