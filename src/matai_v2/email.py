from datetime import datetime
from typing import Iterator, Tuple, Optional, List
from O365 import Account
import logging

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator, Optional, Dict 
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

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

    def __eq__(self, other) -> bool:
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
class EmailContent:

    message_id: str  # Unique identifier for the email
    subject: str
    sender: EmailAddress
    recipients: List[EmailAddress]
    thread_id: str
    timestamp: datetime
    body: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmailContent):
            return NotImplemented
        return (
            self.message_id == other.message_id and
            self.subject == other.subject and
            self.sender == other.sender and
            self.recipients == other.recipients and
            self.thread_id == other.thread_id and
            self.timestamp == other.timestamp and
            self.body == other.body
        )

    def __hash__(self) -> int:
        return hash((
            self.message_id,
            self.subject,
            self.sender,
            tuple(self.recipients),
            self.thread_id,
            self.timestamp,
            self.body
        ))

    def __str__(self) -> str:
        """Return a string representation of the email with main information"""
        divider = "- " * 20
        return (
            f"Message ID: {self.message_id}\n"
            f"Subject: {self.subject}\n"
            f"From: {self.sender.to_string()}\n"
            f"To: {', '.join(r.to_string() for r in self.recipients)}\n"
            f">{divider}"
            f"Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f">{divider}"
        )

    def to_json(self, ) -> Dict:
        """Convert email content to JSON serializable format.
        """
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "sender": self.sender.to_string(),
            "recipients": [r.to_string() for r in self.recipients],
            "thread_id": self.thread_id,
            "timestamp": self.timestamp.isoformat(),
            "body": self.body
        }

    @classmethod
    def from_json(cls, data: Dict) -> 'EmailContent':
        """Convert JSON data to EmailContent object."""
        sender_data = data.get("sender")
        if isinstance(sender_data, dict):
            sender = EmailAddress(**sender_data)
        elif isinstance(sender_data, str):
            sender = EmailAddress.from_string(sender_data)
        else: 
            raise ValueError("Invalid sender format in JSON data")

        recipients_data = data.get("recipients", [])
        recipients: List[EmailAddress] = []
        for r in recipients_data:
            if isinstance(r, dict):
                recipients.append(EmailAddress(**r))
            else:
                recipients.append(EmailAddress.from_string(r))

        thread_id = data.get("thread_id", "")
        ts = data.get("timestamp")
        if isinstance(ts, str):
            try:
                timestamp = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                timestamp = datetime.fromisoformat(ts)
        elif isinstance(ts, datetime):
            timestamp = ts
        else:
            timestamp = datetime.now()

        return cls(
            message_id=data.get("message_id", ""),
            subject=data.get("subject", ""),
            sender=sender,
            recipients=recipients,
            thread_id=thread_id,
            timestamp=timestamp,
            body=data.get("body", "")
        )


class EmailClientInterface(ABC):
    """Abstract interface for email client implementations"""

    @abstractmethod
    def read_messages(self, start_date: Optional[datetime] = None, **kwargs) -> Iterator[EmailContent]:
        """Read all messages and return as EmailContent objects"""
        pass

DEFAULT_SCOPES = ['mailbox', 'mailbox_shared']


class O365Account:

    def __init__(self, credentials: Tuple[str, str], tenant_id: str, scopes: List[str] = DEFAULT_SCOPES):
        self.account = Account(credentials, tenant_id=tenant_id)
        self.scopes = scopes

    def get_auth_link(self):
        assert self.account.con.auth_flow_type in ('authorization', 'public')
        if self.scopes is not None:
            if self.account.con.scopes is not None:
                raise RuntimeError('The scopes must be set either at the Account '
                                   'instantiation or on the account.authenticate method.')
            self.account.con.scopes = self.account.protocol.get_scopes_for(
                self.scopes)
        else:
            if self.account.con.scopes is None:
                raise ValueError(
                    'The scopes are not set. Define the scopes requested.')

        consent_url, flow = self.account.con.get_authorization_url()
        return (consent_url, flow)

    def complete_authentication(self, token_url, **kwargs):
        # TODO: use the flow object to handle the session properly
        if token_url:
            # no need to pass state as the session is the same
            result = self.account.con.request_token(token_url, **kwargs)
            if result:
                logger.debug(
                    'Authentication Flow Completed. Oauth Access Token Stored. You can now use the API.')
            else:
                logger.debug('Something went wrong')

            return bool(result)
        else:
            logger.warning('Authentication Flow aborted.')
            return False

    @property
    def is_authenticated(self):
        return self.account.is_authenticated


class O365EmailClient(EmailClientInterface):
    """O365-specific implementation of email client interface"""

    def __init__(self, authentication_client: O365Account):
        """
        Initialize O365 client 

        Args:
            authentication_client: O365Account: handles the authenthication with the O365 APIs
        """
        self.client = authentication_client

    def authenticated(self) -> bool:
        """Return True if the client is authenticated"""
        return self.client.is_authenticated

    def read_messages(self, start_date: Optional[datetime] = None, limit: int = 100, **kwargs) -> Iterator[EmailContent]:
        """Read messages and convert to EmailContent objects"""
        if not self.authenticated():
            raise RuntimeError("Authentication failed")

        account = self.client.account
        mailbox = account.mailbox()

        # Create query to filter by date if start_date is provided
        query = None
        if start_date:
            query = mailbox.new_query(
                'received_date_time').greater_equal(start_date)

        # Get messages with pagination, requesting in batches of 100
        messages = mailbox.get_messages(query=query, batch=100, limit=limit)

        # Iterate through all pages of messages
        for msg in messages:  # messages is a Pagination object that handles fetching next pages
            try:
                # Convert sender to EmailAddress
                sender = EmailAddress.from_string(
                    f"{msg.sender.name} <{msg.sender.address}>")

                # Convert recipients to EmailAddress objects
                recipients = []
                for recipient in msg.to:
                    recipients.append(EmailAddress.from_string(
                        f"{recipient.name} <{recipient.address}>"))

                # Create EmailContent object
                content = EmailContent(
                    message_id=msg.object_id,  # O365-specific unique message ID
                    subject=msg.subject,
                    sender=sender,
                    recipients=recipients,
                    thread_id=msg.conversation_id,
                    timestamp=msg.received or datetime.now(),
                    body=str(msg)
                )
                content.body = msg.body  # This will trigger clean_body generation
                logger.debug(
                    f"Retrieved message ID={content.message_id}, subject={content.subject}, received={content.timestamp}")

                yield content
            except: 
                logger.error(f"Error parsing email having object: {msg.subject}")
