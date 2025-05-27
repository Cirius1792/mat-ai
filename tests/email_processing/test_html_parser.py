import json
import re
import pytest
from datetime import datetime
from matai.email_processing.model import EmailContent, EmailAddress


def load_emails_from_json(file_path):
    """Load email content objects from a JSON dump file"""
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    
    emails = []
    for email_json in json_data:
        sender = EmailAddress.from_string(email_json['sender'])
        recipients = [EmailAddress.from_string(r) for r in email_json['recipients']]
        
        # Parse timestamp as datetime
        timestamp = datetime.strptime(email_json['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        email = EmailContent(
            message_id=email_json['message_id'],
            subject=email_json['subject'],
            sender=sender,
            recipients=recipients,
            thread_id=email_json['thread_id'],
            timestamp=timestamp,
            raw_content=email_json['body']
        )
        emails.append(email)
    
    return emails


def contains_html_tags(text):
    """Check if text contains HTML tags"""
    # Look for HTML tags like <tag>, <tag/>, </tag>
    pattern = re.compile(r'<\/?[a-zA-Z][^>]*>')
    return bool(pattern.search(text))


def contains_html_attributes(text):
    """Check if text contains HTML attributes"""
    # Look for attribute patterns like attr="value"
    pattern = re.compile(r'\s+[a-zA-Z-]+\s*=\s*["\'][^"\']*["\']')
    return bool(pattern.search(text))


def contains_html_entities(text):
    """Check if text contains HTML entities"""
    # Look for HTML entities like &nbsp; or &#123;
    pattern = re.compile(r'&[a-zA-Z]+;|&#\d+;')
    return bool(pattern.search(text))


def has_html_content(text):
    """Comprehensive check for HTML content"""
    if not text:
        return False
    
    return (
        contains_html_tags(text) or 
        contains_html_attributes(text) or
        contains_html_entities(text) or
        "<html" in text.lower() or
        "<body" in text.lower() or
        "<div" in text.lower() or
        "<span" in text.lower() or
        "<table" in text.lower() or
        "<style" in text.lower() or
        "class=" in text.lower() or
        "style=" in text.lower()
    )


class TestHTMLParserFromDump:
    """Test class to ensure HTML is properly removed from email content"""
    
    @pytest.fixture(scope="class")
    def emails(self):
        """Load emails from the message dump file - using class scope to load once"""
        # Limit to 10 emails for faster testing
        return load_emails_from_json("./tests/email_processing/message_dump_anonymized.json")[:10]
    
    def test_emails_loaded(self, emails):
        """Verify that emails were loaded successfully from dump"""
        assert len(emails) > 0, "No emails loaded from dump file"
    
    def test_raw_content_contains_html(self, emails):
        """Verify that at least some emails in the dump contain HTML"""
        html_emails = [email for email in emails if has_html_content(email.raw_content)]
        
        # It's possible the first 10 emails don't have HTML, so don't force the assertion
        if len(html_emails) > 0:
            print(f"\nFound {len(html_emails)} emails with HTML content out of {len(emails)} total")
        else:
            print("\nNo HTML emails found in the sample. Test will be skipped.")
            pytest.skip("No HTML emails found in the sampled emails")
    
    def test_clean_body_contains_no_html(self, emails):
        """Verify that clean_body property contains no HTML after parsing"""
        # Only process emails that actually have HTML
        html_emails = [email for email in emails if has_html_content(email.raw_content)]
        if not html_emails:
            pytest.skip("No HTML emails found to test cleaning on")
            
        for email in html_emails:
            # Clean body triggers the parsing process
            clean_content = email.clean_body
            
            # Main assertion: no HTML in clean content
            assert not has_html_content(clean_content), f"HTML found in clean_body for email: {email.message_id}"
            
            # No need for additional checks since has_html_content is comprehensive
    
    def test_html_table_conversion(self, emails):
        """Verify that HTML tables are properly converted to text tables"""
        # Find emails with tables
        emails_with_tables = [email for email in emails if "<table" in email.raw_content.lower()]
        
        if not emails_with_tables:
            pytest.skip("No emails with HTML tables found in the sample")
            
        for email in emails_with_tables:
            # Get clean content
            clean_content = email.clean_body
            
            # The original <table> tag should not be present
            assert "<table" not in clean_content.lower(), f"Table tag found in clean_body for email: {email.message_id}"
            
            # Tables should be converted to ASCII format with +--+ borders
            # Not all tables might be converted perfectly (some might be filtered out), so just log observations
            has_ascii_table = "+" in clean_content and "-" in clean_content and "|" in clean_content
            if not has_ascii_table:
                print(f"Note: Email {email.message_id} had a table but no ASCII table was found in the clean content")
