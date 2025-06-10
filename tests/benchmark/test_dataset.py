from unittest import TestCase
from datetime import datetime

from benchmark.dataset import Dataset, DatasetLine
from matai.email_processing.model import ActionItem, ActionType, EmailAddress, EmailContent, Participant


class TestDataset(TestCase):
    def setUp(self) -> None:
        self.dataset = Dataset()
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
            message_id=email.message_id,
            confidence_score=1.0
        )

    def test_should_add_a_new_entry_to_the_dataset(self):
        stored_entries = self.dataset.load()
        previously_stored = len(stored_entries)
        dataset_line = DatasetLine(self.email, self.action_item)
        self.dataset.append(dataset_line)

        stored_entries = self.dataset.load()
        self.assertEqual(len(stored_entries), previously_stored+1)

        stored_line = stored_entries[-1]
        self.assertEqual(dataset_line, stored_line)
