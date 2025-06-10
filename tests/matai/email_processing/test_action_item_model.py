import unittest
from datetime import datetime
from matai.email_processing.model import ActionItem, ActionType, Participant


class ActionItemTest(unittest.TestCase):
    def setUp(self):
        self.sample_datetime = datetime(2025, 6, 15)
        self.owners = [Participant(alias="alice"), Participant(alias="bob")]
        self.waiters = [Participant(alias="carol")]
        self.metadata = {"project": "p1", "thread_id": "t1"}
        self.action_item = ActionItem(
            action_type=ActionType.TASK,
            description="Do something",
            confidence_score=0.75,
            message_id="msg-1",
            due_date=self.sample_datetime,
            owners=self.owners,
            waiters=self.waiters,
            metadata=self.metadata,
            id=10
        )
        self.json_data = self.action_item.to_json()
        self.from_json_inst = ActionItem.from_json(self.json_data)

    def test_to_json(self):
        self.assertEqual(self.json_data["id"], 10)
        self.assertEqual(self.json_data["action_type"], "TASK")
        self.assertEqual(self.json_data["description"], "Do something")
        self.assertEqual(self.json_data["due_date"], "2025-06-15")
        self.assertEqual(self.json_data["owners"], ["alice", "bob"])
        self.assertEqual(self.json_data["waiters"], ["carol"])
        self.assertEqual(self.json_data["confidence_score"], 0.75)
        self.assertEqual(self.json_data["message_id"], "msg-1")

    def test_from_json_defaults(self):
        inst = self.from_json_inst
        self.assertIsInstance(inst, ActionItem)
        self.assertEqual(inst.id, 0)
        self.assertEqual(inst.action_type, ActionType.TASK)
        self.assertEqual(inst.description, "Do something")
        self.assertEqual(inst.confidence_score, 0.75)
        self.assertEqual(inst.message_id, "msg-1")
        self.assertEqual(inst.due_date, self.sample_datetime)
        self.assertEqual([p.alias for p in inst.owners], ["alice", "bob"])
        self.assertEqual([p.alias for p in inst.waiters], ["carol"])
        self.assertEqual(inst.metadata, {})

    def test_str_contains_main_fields(self):
        s = str(self.action_item)
        self.assertIn("ID: 10", s)
        self.assertIn("Type: TASK", s)
        self.assertIn("Description: Do something", s)
        self.assertIn("Due Date: 2025-06-15", s)
        self.assertIn("Owners: alice, bob", s)
        self.assertIn("Waiters: carol", s)
        self.assertIn("Confidence: 0.75", s)
