from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from matai.email_processing.model import ActionItem, EmailContent, Participant


class ActionItemDAO(ABC):
    @abstractmethod
    def create_action_item(self, action_item: ActionItem) -> None:
        pass

    @abstractmethod
    def get_action_item(self, action_item_id: int) -> Optional[ActionItem]:
        pass

    @abstractmethod
    def update_action_item(self, action_item: ActionItem) -> None:
        pass

    @abstractmethod
    def delete_action_item(self, action_item_id: int) -> None:
        pass

    @abstractmethod
    def delete_all_action_items(self) -> None:
        pass

    @abstractmethod
    def list_action_items(self) -> List[ActionItem]:
        pass


class EmailContentDAO(ABC):
    @abstractmethod
    def create_email_content(self, email_content: EmailContent) -> None:
        pass

    @abstractmethod
    def get_email_content(self, message_id: str) -> Optional[EmailContent]:
        pass

    @abstractmethod
    def update_email_content(self, email_content: EmailContent) -> None:
        pass

    @abstractmethod
    def delete_email_content(self, message_id: str) -> None:
        pass

    @abstractmethod
    def list_email_contents(self, timestamp_from: Optional[datetime] = None) -> List[EmailContent]:
        pass

    @abstractmethod
    def delete_all_email_contents(self) -> None:
        pass


class ParticipantDAO(ABC):
    @abstractmethod
    def create_participant(self, participant: Participant) -> None:
        pass

    @abstractmethod
    def get_participant(self, alias: str) -> Optional[Participant]:
        pass

    @abstractmethod
    def update_participant(self, participant: Participant) -> None:
        pass

    @abstractmethod
    def delete_participant(self, alias: str) -> None:
        pass

    @abstractmethod
    def delete_all_participants(self) -> None:
        pass

    @abstractmethod
    def list_participants(self) -> List[Participant]:
        pass
