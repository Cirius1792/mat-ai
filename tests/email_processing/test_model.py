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
