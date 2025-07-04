
import unittest
from datetime import datetime, timedelta
from matai_v2.store import EmailStore


class TestEmailStore(unittest.TestCase):

    def setUp(self):
        # Use an in-memory SQLite database for testing
        self.db_path = ":memory:"
        self.store = EmailStore(self.db_path)

    def tearDown(self):
        self.store.close()

    def test_initialization_creates_table(self):
        # Check if the table was created
        self.store.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='PROCESSED_EMAIL'")
        self.assertIsNotNone(self.store.cursor.fetchone())

    def test_store_and_was_processed(self):
        message_id = "test_message_1"
        message_date = datetime.now()

        # Initially, it should not be processed
        self.assertFalse(self.store.was_processed(message_id))

        # Store the email
        self.store.store(message_id, message_date, "PROCESSED")

        # Now it should be processed
        self.assertTrue(self.store.was_processed(message_id))

    def test_retrieve_from(self):
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        self.store.store("msg1", yesterday, "PROCESSED")
        self.store.store("msg2", now, "PROCESSED")
        self.store.store("msg3", tomorrow, "PROCESSED")

        # Retrieve records from today onwards
        records = self.store.retrieve_from(now)

        self.assertEqual(len(records), 2)

        retrieved_ids = [record[0] for record in records]
        self.assertIn("msg2", retrieved_ids)
        self.assertIn("msg3", retrieved_ids)
        self.assertNotIn("msg1", retrieved_ids)

    def test_store_with_optional_process_date(self):
        message_id = "test_message_2"
        message_date = datetime.now()
        process_date = datetime(2023, 1, 1, 12, 0, 0)

        self.store.store(message_id, message_date, "SKIPPED", process_date)

        self.store.cursor.execute(
            "SELECT process_date FROM PROCESSED_EMAIL WHERE message_id=?", (message_id,))
        stored_process_date_str = self.store.cursor.fetchone()[0]
        stored_process_date = datetime.fromisoformat(stored_process_date_str)

        self.assertEqual(stored_process_date, process_date)


if __name__ == '__main__':
    unittest.main()
