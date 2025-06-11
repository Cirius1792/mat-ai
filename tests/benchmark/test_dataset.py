from unittest import TestCase
from datetime import datetime

from matai.benchmark.dataset import Dataset, DatasetLine
from matai.email_processing.model import ActionItem, ActionType, EmailAddress, EmailContent
import tempfile


class TestDataset(TestCase):
    def setUp(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile()
        self.dataset = Dataset(file_path=self.temp_file.name)
        self.temp_file.close()
        self.email: EmailContent = EmailContent(message_id='1',
                                                subject="Kind Reminder",
                                                sender=EmailAddress.from_string(
                                                    "user1@company.com"),
                                                recipients=[EmailAddress.from_string(
                                                    "user2@company.com")],
                                                thread_id='t1',
                                                timestamp=datetime.now(),
                                                raw_content="""Hi,
                                           This message is just to remind you to send the report I asked you yesterday in time for the meeting of tomorrow morning.

                                           Regards
                                           User1
                                           """)
        self.action_item: ActionItem = ActionItem(
            action_type=ActionType.TASK,
            description="Send the requested report in time for the meeting",
            message_id=self.email.message_id,
            confidence_score=1.0,
            due_date=datetime.strptime("2025-10-23", '%Y-%m-%d'),
            owners=[],
            waiters=[],
            metadata={}
        )


    def test_should_add_a_new_entry_to_the_dataset(self):
        stored_entries = self.dataset.load()
        previously_stored = len(stored_entries)
        dataset_line = DatasetLine(self.email, [self.action_item])
        self.dataset.append(dataset_line)

        stored_entries = self.dataset.load()
        self.assertEqual(len(stored_entries), previously_stored+1)

        stored_line = stored_entries[-1]
        self.assertEqual(dataset_line, stored_line)

    def test_should_overwrite_file_with_updated_lines(self):
        # append two entries
        first_line = DatasetLine(self.email, [self.action_item])
        self.dataset.append(first_line)
        second_email = EmailContent(
            message_id='2',
            subject='Second',
            sender=EmailAddress.from_string("user3@company.com"),
            recipients=[EmailAddress.from_string("user4@company.com")],
            thread_id='t2',
            timestamp=self.email.timestamp,
            raw_content="content2"
        )
        second_action = ActionItem(
            action_type=ActionType.DECISION,
            description="decision desc",
            message_id=second_email.message_id,
            confidence_score=0.75,
            due_date=None,
            owners=[],
            waiters=[],
            metadata={}
        )
        second_line = DatasetLine(second_email, [second_action])
        self.dataset.append(second_line)

        lines = self.dataset.load()
        lines[0].email.subject = "Modified"
        self.dataset.save(lines)

        new_lines = self.dataset.load()
        self.assertEqual(2, len(new_lines))
        self.assertEqual(new_lines[0].email.subject, "Modified")
        self.assertEqual(len(new_lines), 2)
        self.assertEqual(new_lines[1], second_line)

    def test_should_preserve_email_timestamp_and_action_type(self):
        custom_dt = datetime(2022, 1, 1, 9, 0, 0)
        self.email.timestamp = custom_dt
        self.action_item.due_date = None
        line = DatasetLine(self.email, [self.action_item])
        self.dataset.save([line])
        loaded = self.dataset.load()
        self.assertEqual(loaded[0].email.timestamp, custom_dt)
        self.assertEqual(
            loaded[0].expected_action_items[0].action_type,
            self.action_item.action_type
        )
