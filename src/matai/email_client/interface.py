from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator, Optional
from ..email_processing.model import EmailContent


class EmailClientInterface(ABC):
    """Abstract interface for email client implementations"""

    @abstractmethod
    def read_messages(self, start_date: Optional[datetime] = None, **kwargs) -> Iterator[EmailContent]:
        """Read all messages and return as EmailContent objects"""
        pass
