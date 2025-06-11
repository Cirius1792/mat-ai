import unittest
from datetime import datetime
from matai.email_processing.model import EmailContent, ActionItem, ActionType, Participant

class EmailContentTest(unittest.TestCase):
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

    def test_unique_id(self):
        expected = f"{self.raw_data['message_id']}_{self.raw_data['thread_id']}"
        self.assertEqual(self.email.unique_id, expected)

    def test_body_property(self):
        self.assertEqual(self.email.body, self.raw_data["body"])

    def test_csv_header(self):
        self.assertEqual(EmailContent.csv_header(), EmailContent.CSV_HEADER)

    def test_to_csv(self):
        csv = self.email.to_csv()
        self.assertEqual(csv[0], self.email.message_id)
        self.assertEqual(csv[1], self.email.subject)
        self.assertEqual(csv[2], self.email.sender.to_string())
        self.assertEqual(csv[3], self.email.body)

    def test_str(self):
        s = str(self.email)
        self.assertIn(self.email.message_id, s)
        self.assertIn(self.email.subject, s)
        self.assertIn(self.email.sender.email, s)

    def test_clean_body(self):
        clean = self.email.clean_body
        self.assertNotIn('<p>', clean)
        self.assertNotIn('</p>', clean)
        self.assertIn('Hello World', clean)

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
        self.assertEqual(email.raw_content, html)
        self.assertEqual(email.body, html)

    def test_from_json_prefers_raw_content(self):
        # Should prefer raw_content over body field
        ts = "2025-06-10 12:00:00"
        raw_html = "<div>Raw Content</div>"
        body_html = "<p>Body Content</p>"
        data = {
            "message_id": "id-raw",
            "subject": "Raw Content Test",
            "sender": "user@example.com",
            "recipients": ["user2@example.com"],
            "thread_id": "thread-raw",
            "timestamp": ts,
            "raw_content": raw_html,
            "body": body_html
        }
        email = EmailContent.from_json(data)
        self.assertEqual(email.raw_content, raw_html)
        self.assertEqual(email.body, raw_html)

