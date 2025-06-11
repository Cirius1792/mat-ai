from unittest import TestCase

from matai.email_processing.model import EmailAddress


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
    def test_eq_and_hash_ignore_internal_fields(self):
        from datetime import datetime
        from matai.email_processing.model import EmailContent

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
            raw_content="body"
        )
        e2 = EmailContent(
            message_id="id1",
            subject="subj",
            sender=sender,
            recipients=[recipient],
            thread_id="tid",
            timestamp=timestamp,
            raw_content="body"
        )
        # compute clean_body to change internal state
        _ = e1.clean_body
        e2._body = None
        self.assertEqual(e1, e2)
        self.assertEqual(hash(e1), hash(e2))
