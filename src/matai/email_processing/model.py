
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import re


@dataclass
class EmailAddress:
    email: str
    name: Optional[str]
    domain: str

    @classmethod
    def from_string(cls, email_string: str) -> 'EmailAddress':
        """
        Create EmailAddress from string format 'Name <email@domain.com>'
        or plain 'email@domain.com'
        """

        # Match either "Name <email@domain.com>" or "email@domain.com"
        pattern = r'^(?:([^<]*?)\s*<)?([^>]*@[^>]*)>?$'
        match = re.match(pattern, email_string.strip())

        if not match:
            raise ValueError(f"Invalid email format: {email_string}")

        name, email = match.groups()

        # Extract domain from email
        domain = email.split('@')[1]

        return cls(email=email, name=name, domain=domain)

    def to_string(self) -> str:
        """
        Convert to string representation.
        Returns format: 'Name <email@domain.com>' if name exists,
        otherwise just 'email@domain.com'
        """
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email

    def __eq__(self, other: 'EmailAddress') -> bool:
        """
        Equality comparison based on email address only,
        ignoring display name
        """
        return self.email.lower() == other.email.lower()

    def __hash__(self) -> int:
        """
        Hash based on lowercase email for dictionary/set operations
        """
        return hash(self.email.lower())


@dataclass
class Participant:
    alias: str
    email: Optional[EmailAddress] = None


@dataclass
class EmailContent:
    CSV_HEADER = ["message_id", "subject", "sender",
                  "recipients", "thread_id", "timestamp", "clean_body"]

    message_id: str  # Unique identifier for the email
    subject: str
    sender: EmailAddress
    recipients: List[EmailAddress]
    thread_id: str
    timestamp: datetime
    raw_content: str
    _body: Optional[str] = None
    _clean_body: Optional[str] = None

    @property
    def unique_id(self) -> str:
        """
        Generate a unique identifier combining message_id and thread_id
        This ensures uniqueness even across different email threads
        """
        return f"{self.message_id}_{self.thread_id}"

    @property
    def body(self) -> str:
        """Get the original message body"""
        if self._body is None:
            self._body = self.raw_content
        return self._body

    @body.setter
    def body(self, value: str):
        """Set the body and reset clean_body cache"""
        self._body = value
        self._clean_body = None

    @classmethod
    def csv_header(cls) -> List[str]:
        """Get the header for CSV export"""
        return cls.CSV_HEADER

    @property
    def clean_body(self) -> str:
        """Get cleaned message body with quoted text removed"""
        if self._clean_body is None:
            from .parser import EmailParser
            self._clean_body = EmailParser.clean_body(
                self.body, self.message_id)
        return self._clean_body

    def __str__(self) -> str:
        """Return a string representation of the email with main information"""
        divider = "- " * 20
        return (
            f"Message ID: {self.message_id}\n"
            f"Subject: {self.subject}\n"
            f"From: {self.sender.to_string()}\n"
            f"To: {', '.join(r.to_string() for r in self.recipients)}\n"
            f">{divider}"
            f"\n{self.clean_body}\n"
            f"Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f">{divider}"
        )

    def to_csv(self) -> List[str]:
        """Convert email content to CSV format returning the csv row ready to be written.
        If the separator character is present in the text fields, they are escaped to avoid problem when writing the csv
        """
        return [
            self.message_id,
            self.subject,
            self.sender.email,
            ', '.join(r.email for r in self.recipients),
            self.thread_id,
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.clean_body,
        ]

    def to_json(self, ) -> Dict:
        """Convert email content to JSON serializable format.

        """
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "sender": self.sender.to_string(),
            "recipients": [r.to_string() for r in self.recipients],
            "thread_id": self.thread_id,
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "body": self.body
        }


class ActionType (Enum):
    DEADLINE = 1
    TASK = 2
    MEETING = 3
    DECISION = 4
    INFORMATION = 5

    @classmethod
    def from_string(cls, text: str) -> 'ActionType':
        text = text.lower()
        if text == 'deadline':
            return ActionType.DEADLINE
        elif text == 'task':
            return ActionType.TASK
        elif text == 'meeting':
            return ActionType.MEETING
        elif text == 'decision':
            return ActionType.DECISION
        elif text == 'information':
            return ActionType.INFORMATION
        else:
            raise ValueError(f"Invalid action type: {text}")


@dataclass
class ActionItem:
    """An action item is a call to action extracted from an email.
        It includes details like description, due date, owners, and confidence score.
    """
    action_type: ActionType  # Enum: DEADLINE, TASK, etc.
    description: str
    confidence_score: float
    message_id: str
    due_date: Optional[datetime]
    owners: List[Participant]
    waiters: List[Participant]
    metadata: Dict[str, str]
    id: int = 0

    CSV_HEADER = ["id", "message_id", "type", "description",
                  "due_date", "owners", "waiters", "confidence"]

    def __str__(self) -> str:
        return (
            f"Action Item:\n"
            f"  ID: {self.id}\n"
            f"  Type: {self.action_type.name}\n"
            f"  Description: {self.description}\n"
            f"  Due Date: {self.due_date.strftime('%Y-%m-%d') if self.due_date else 'None'}\n"
            f"  Owners: {', '.join(p.alias for p in self.owners)}\n"
            f"  Waiters: {', '.join(p.alias for p in self.waiters)}\n"
            f"  Confidence: {self.confidence_score}\n"
        )

    def to_json(self) -> Dict:
        """Convert action item to JSON serializable format."""
        return {
            "id": self.id,
            "action_type": self.action_type.name,
            "description": self.description,
            "due_date": self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            "owners": [owner.alias for owner in self.owners],
            "waiters": [waiter.alias for waiter in self.waiters],
            "confidence_score": self.confidence_score,
            "message_id": self.message_id
        }


class Priority (Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class ActionMetadata:
    project: Optional[str]
    thread_id: str
    priority: Optional[Priority]  # Enum: HIGH, MEDIUM, LOW
    tags: List[str]
    context: str
    creation_date: datetime
    last_modified: datetime
