import pytest

from matai_v2.parser import clean_body

# Define test cases for different languages and separators
test_cases = [
    (
        "<html><body><table><tr><th>Name</th><th>Age</th></tr><tr><td>Alice</td><td>30</td></tr><tr><td>Bob</td><td>25</td></tr></table></body></html>",
        "+-------+-----+\n| Name | Age |\n+-------+-----+\n| Alice | 30 |\n| Bob | 25 |\n+-------+-----+",
        "HTML Table"
    ),
    # ("Hello,\n\nThis is the latest message.\n\nFrom:\nPrevious message", "Hello,\n\nThis is the latest message.", "English - From"),
    # ("Hello,\n\nThis is the latest message.\n\nSent:\nPrevious message", "Hello,\n\nThis is the latest message.", "English - Sent"),
    # ("Hello,\n\nThis is the latest message.\n\nTo:\nPrevious message", "Hello,\n\nThis is the latest message.", "English - To"),
    # ("Hello,\n\nThis is the latest message.\n\nSubject:\nPrevious message", "Hello,\n\nThis is the latest message.", "English - Subject"),
]

@pytest.mark.parametrize("email_body, expected_clean_body, language", test_cases)
def test_clean_body(email_body, expected_clean_body, language):
    cleaned_body = clean_body(email_body)
    assert cleaned_body == expected_clean_body, f"Failed for language: {language}"

