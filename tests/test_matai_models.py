from unittest import TestCase

from datetime import datetime
from matai_v2.email import EmailAddress, EmailContent
from matai_v2.processor import ActionItem, ActionType, load_action_item_from_json



class EmailTestCase(TestCase):
    def test_should_parse_a_valid_email_address_in_plain_format(self):
        domain = "domain.com"
        prefix = "test.test"
        email_address_string = f"{prefix}@{domain}"
        email = EmailAddress.from_string(email_address_string)
        self.assertEqual(domain, email.domain)
        self.assertEqual(None, email.name)

    def test_should_parse_a_valid_email_address_in_email_format(self):
        domain = "domain.com"
        name = "Test Test"
        prefix = "test.test"
        email_address_string = f"{name} <{prefix}@{domain}>"
        email = EmailAddress.from_string(email_address_string)
        self.assertEqual(domain, email.domain)
        self.assertEqual(name, email.name)


class EmailContentTestCase(TestCase):
    def test_eq_and_hash(self):

        sender = EmailAddress.from_string("a@b.com")
        recipient = EmailAddress.from_string("c@d.com")
        timestamp = datetime(2025, 1, 1, 12, 0, 0)

        e1 = EmailContent(
            message_id="id1",
            subject="subj",
            sender=sender,
            recipients=[recipient],
            thread_id="tid",
            timestamp=timestamp,
            body="body"
        )
        e2 = EmailContent(
            message_id="id1",
            subject="subj",
            sender=sender,
            recipients=[recipient],
            thread_id="tid",
            timestamp=timestamp,
            body="body"
        )
        # compute clean_body to change internal state
        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))

    def test_eq_and_hash_for_different_instances(self):

        sender = EmailAddress.from_string("a@b.com")
        recipient = EmailAddress.from_string("c@d.com")
        timestamp = datetime(2025, 1, 1, 12, 0, 0)

        e1 = EmailContent(
            message_id="id1",
            subject="subj",
            sender=sender,
            recipients=[recipient],
            thread_id="tid",
            timestamp=timestamp,
            body="body"
        )
        # compute clean_body to change internal state
        self.assertNotEqual(e1, "others")

class EmailContentTest(TestCase):
    
    def setUp(self):
        self.raw_data = {
            "message_id": "id-123",
            "subject": "Test Email",
            "sender": "sender@example.com",
            "recipients": ["recipient1@example.com", "Recipient Two <recipient2@example.com>"],
            "thread_id": "thread-1",
            "timestamp": "2025-06-10 12:34:56",
            "body": "<p>Hello <strong>World</strong></p>"
        }
        self.email = EmailContent.from_json(self.raw_data)
        self.email.body = self.raw_data["body"]

    def test_from_json(self):
        inst = EmailContent.from_json(self.raw_data)
        self.assertIsInstance(inst, EmailContent)

    def test_body_property(self):
        self.assertEqual(self.email.body, self.raw_data["body"])


    def test_str(self):
        s = str(self.email)
        self.assertIn(self.email.message_id, s)
        self.assertIn(self.email.subject, s)
        self.assertIn(self.email.sender.email, s)

    def test_recipients_and_timestamp(self):
        self.assertEqual(len(self.email.recipients), 2)
        self.assertEqual(self.email.recipients[0].email, "recipient1@example.com")
        self.assertEqual(self.email.recipients[1].name, "Recipient Two")
        self.assertEqual(self.email.thread_id, "thread-1")
        self.assertEqual(self.email.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "2025-06-10 12:34:56")

    def test_to_json(self):
        json_data = self.email.to_json()
        self.assertEqual(json_data["message_id"], self.email.message_id)
        self.assertEqual(json_data["subject"], self.email.subject)
        self.assertEqual(json_data["sender"], self.email.sender.to_string())
        self.assertEqual(json_data["recipients"], [r.to_string() for r in self.email.recipients])
        self.assertEqual(json_data["thread_id"], self.email.thread_id)
        self.assertEqual(json_data["timestamp"], self.email.timestamp.isoformat())
        self.assertEqual(json_data["body"], self.email.body)

    def test_from_json_iso_timestamp(self):
        # Should correctly parse ISO-format timestamp from body field
        iso_ts = "2025-06-10T07:49:25.299945"
        html = "<p>Test ISO</p>"
        data = {
            "message_id": "id-iso-ts",
            "subject": "ISO Timestamp Test",
            "sender": "user@example.com",
            "recipients": ["user2@example.com"],
            "thread_id": "thread-iso",
            "timestamp": iso_ts,
            "body": html
        }
        email = EmailContent.from_json(data)
        self.assertIsInstance(email.timestamp, datetime)
        self.assertEqual(email.timestamp.isoformat(), iso_ts)
        self.assertEqual(email.body, html)

    def test_from_json_prefers_raw_content(self):
        # Should prefer raw_content over body field
        ts = "2025-06-10 12:00:00"
        body_html = "<p>Body Content</p>"
        data = {
            "message_id": "id-raw",
            "subject": "Raw Content Test",
            "sender": "user@example.com",
            "recipients": ["user2@example.com"],
            "thread_id": "thread-raw",
            "timestamp": ts,
            "body": body_html
        }
        email = EmailContent.from_json(data)
        self.assertEqual(email.body, body_html)

class ActionItemTest(TestCase):
    def setUp(self):
        self.sample_datetime = datetime(2025, 6, 15)
        self.metadata = {"project": "p1", "thread_id": "t1"}
        self.action_item = ActionItem(
            action_type=ActionType.TASK,
            description="Do something",
            confidence_score=0.75,
            message_id="msg-1",
            due_date=self.sample_datetime,
            id=10
        )
        self.json_data = self.action_item.to_json()
        self.from_json_inst = load_action_item_from_json(self.json_data)

    def test_to_json(self):
        self.assertEqual(self.json_data["id"], 10)
        self.assertEqual(self.json_data["action_type"], "TASK")
        self.assertEqual(self.json_data["description"], "Do something")
        self.assertEqual(self.json_data["due_date"], "2025-06-15T00:00:00")
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

    def test_str_contains_main_fields(self):
        s = str(self.action_item)
        self.assertIn("ID: 10", s)
        self.assertIn("Type: TASK", s)
        self.assertIn("Description: Do something", s)
        self.assertIn("Due Date: 2025-06-15", s)
        self.assertIn("Confidence: 0.75", s)


