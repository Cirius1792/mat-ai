import pytest
from typing import Tuple
from datetime import datetime
from unittest.mock import MagicMock
from matai.email_processing.model import EmailContent, EmailAddress, ActionType
from matai.email_processing.processor import EmailProcessor

# Define test cases covering various outcomes
test_cases = [
    (
        # Test case: Single owner (email address) and single waiter (email address) with action type "task"
        EmailContent(
            message_id="test_1",
            subject="Task Test",
            sender=EmailAddress("noreply@example.com", None, "example.com"),
            recipients=[],
            thread_id="111",
            timestamp=datetime(2025, 2, 20),
            raw_content="Email content for task test."
        ),
        '{"action_items": [{"description": "Task email test", "due_date": "2025-02-20", "owners": ["mario.rossi@email"], "waiters": ["anna.bianchi@example.com"], "confidence": 0.95, "type": "task"}]}',
        {
            "description": "Task email test",
            "due_date": "2025-02-20",
            "owners": ["mario.rossi@email"],
            "waiters": ["anna.bianchi@example.com"],
            "confidence": 0.95,
            "action_type": ActionType.TASK
        }
    ),
    (
        # Test case: Owners and waiters as labels ("group A", "group B") with type "deadline"
        EmailContent(
            message_id="test_2",
            subject="Deadline Test",
            sender=EmailAddress("noreply@example.com", None, "example.com"),
            recipients=[],
            thread_id="222",
            timestamp=datetime(2025, 2, 20),
            raw_content="Email content for deadline test."
        ),
        '{"action_items": [{"description": "Deadline email test", "due_date": "2025-02-21", "owners": ["group A"], "waiters": ["group B"], "confidence": 0.9, "type": "deadline"}]}',
        {
            "description": "Deadline email test",
            "due_date": "2025-02-21",
            "owners": ["group A"],
            "waiters": ["group B"],
            "confidence": 0.9,
            "action_type": ActionType.DEADLINE
        }
    ),
    (
        # Test case: Action type "meeting" with owners as a label and waiter as an email address
        EmailContent(
            message_id="test_3",
            subject="Meeting Test",
            sender=EmailAddress("noreply@example.com", None, "example.com"),
            recipients=[],
            thread_id="333",
            timestamp=datetime(2025, 2, 20),
            raw_content="Email content for meeting test."
        ),
        '{"action_items": [{"description": "Meeting email test", "due_date": "2025-02-22", "owners": ["group A"], "waiters": ["mario.rossi@email"], "confidence": 0.85, "type": "meeting"}]}',
        {
            "description": "Meeting email test",
            "due_date": "2025-02-22",
            "owners": ["group A"],
            "waiters": ["mario.rossi@email"],
            "confidence": 0.85,
            "action_type": ActionType.MEETING
        }
    ),
    (
        # Test case: Action type "decision" with owner as an email address and waiter as a label
        EmailContent(
            message_id="test_4",
            subject="Decision Test",
            sender=EmailAddress("noreply@example.com", None, "example.com"),
            recipients=[],
            thread_id="444",
            timestamp=datetime(2025, 2, 20),
            raw_content="Email content for decision test."
        ),
        '{"action_items": [{"description": "Decision email test", "due_date": "2025-02-23", "owners": ["mario.rossi@email"], "waiters": ["group B"], "confidence": 0.92, "type": "decision"}]}',
        {
            "description": "Decision email test",
            "due_date": "2025-02-23",
            "owners": ["mario.rossi@email"],
            "waiters": ["group B"],
            "confidence": 0.92,
            "action_type": ActionType.DECISION
        }
    ),
    (
        # Test case: Missing "type" field should default to "task" (Information case)
        EmailContent(
            message_id="test_5",
            subject="Information Test",
            sender=EmailAddress("noreply@example.com", None, "example.com"),
            recipients=[],
            thread_id="555",
            timestamp=datetime(2025, 2, 20),
            raw_content="Email content for information test."
        ),
        '{"action_items": [{"description": "Information email test", "due_date": "2025-02-24", "owners": ["group C"], "waiters": ["group D"], "confidence": 0.80}]}',
        {
            "description": "Information email test",
            "due_date": "2025-02-24",
            "owners": ["group C"],
            "waiters": ["group D"],
            "confidence": 0.80,
            "action_type": ActionType.TASK
        }
    )
]

@pytest.fixture
def processor()-> Tuple[EmailProcessor, MagicMock]:
    mock_llm = MagicMock()
    proc = EmailProcessor(
        client=mock_llm,
        model="test_model",
        confidence_threshold=0.85
    )
    return proc, mock_llm

@pytest.mark.parametrize("sample_email, llm_response_content, expected", test_cases)
def test_email_processor_parametrized(processor:Tuple[EmailProcessor, MagicMock], sample_email, llm_response_content, expected):
    proc, mock_llm = processor
    mock_llm.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(content=llm_response_content)
        )]
    )
    results = proc.process_email(sample_email)
    # Ensure one action item is returned
    assert len(results) == 1
    result = results[0]
    assert result.description == expected["description"]
    assert result.due_date.strftime("%Y-%m-%d") == expected["due_date"]
    # Check owners and waiters (list of Participant.alias values)
    owners_aliases = [p.alias for p in result.owners]
    waiters_aliases = [p.alias for p in result.waiters]
    assert owners_aliases == expected["owners"]
    assert waiters_aliases == expected["waiters"]
    assert abs(result.confidence_score - expected["confidence"]) < 0.01
    assert result.action_type == expected["action_type"]
