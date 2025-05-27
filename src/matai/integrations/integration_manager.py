# This script is the glue between the core application and the third party integrations.
# It is responsible for authenticating with the chosen board and handling the creation of new action items on it
import logging
from typing import Optional
from datetime import datetime
from matai.email_processing.model import EmailAddress, Participant

from matai.email_processing.model import ActionItem, EmailContent, ActionType
from matai.integrations.trello import TrelloClient
from matai.manager.manager import ActionableEmails

logger = logging.getLogger(__name__)


class IntegrationManager:
    def __init__(self, client: TrelloClient,
                 board_id: str,
                 app_board: str = "Mantis"):
        self._client = client
        self._board_id = board_id
        self._app_board = app_board
        self._list_id = None

    @property
    def list_id(self) -> Optional[str]:
        return self._list_id

    @list_id.setter
    def list_id(self, value):
        self._list_id = value

    def _create_card_description(self, email: EmailContent, action_item: ActionItem) -> str:
        return f"Thread Subject: {email.subject}\nOriginal Message: \n{email.clean_body}" 

    def setup(self):
        """
        Set up the target board by ensuring the presence of a specific list.

        This method checks if the target board already contains a list named
        according to the `self._app_board` attribute. If the list does not exist,
        it creates a new list with that name. 
        The list ID is stored in `self.list_id`.
        """
        # Check if the target board already has the mantis list
        board_lists = self._client.lists(self._board_id)
        is_configured = any(
            [board_list.name == self._app_board for board_list in board_lists])

        # If there is no mantis list, it creates it
        if not is_configured:
            logger.info("No list %s found in board %s. Creating it...",
                        self._app_board, self._board_id)
            default_list = self._client.create_list(self._board_id, "Mantis")
            self.list_id = default_list.id
            logger.info("List %s created with ID %s",
                        self._app_board, self.list_id)
        else:
            self.list_id = next(
                board_list.id for board_list in board_lists if board_list.name == self._app_board)
            assert self.list_id is not None, "List ID must be set before creating tasks"
            logger.info("List %s found with ID %s",
                        self._app_board, self.list_id)

    def _create_card_name(self, action_item: ActionItem) -> str:
        return f"{action_item.action_type.name}: {action_item.description}"

    def create_tasks(self, actionable_items: ActionableEmails):
        if self.list_id is None:
            self.setup()

        assert self.list_id is not None, "List ID must be set before creating tasks"
        email = actionable_items[0]
        for action_item in actionable_items[1]:
            description = self._create_card_description(email, action_item)
            name = self._create_card_name(action_item)
            due_date = action_item.due_date if action_item.due_date else None
            logger.info("Creating card in list %s with name %s",
                        self._app_board, name)
            logger.info("Card description: %s", description)
            card = self._client.create_card(
                self.list_id, name, description, due_date)
            logger.info("Created card %s in list %s",
                        card.name, self._app_board)


if __name__ == "__main__":
    import os
    api_key = os.environ["TRELLO_API_KEY"]
    token = os.environ["TRELLO_API_TOKEN"]
    board_id = os.environ["TRELLO_BOARD_ID"]
    client = TrelloClient(
        api_key, token)
    im = IntegrationManager(client, board_id)
    # Initialize an ActionableItem for test purposes
    email_content = EmailContent(
        message_id="test_message_id",
        subject="Test Subject",
        sender=EmailAddress(email="sender@example.com",
                            name="Sender Name", domain="example.com"),
        recipients=[EmailAddress(
            email="recipient@example.com", name="Recipient Name", domain="example.com")],
        thread_id="test_thread_id",
        timestamp=datetime.now(),
        raw_content="This is a test email body."
    )
    action_item = ActionItem(
        action_type=ActionType.DEADLINE,
        description="Test action item",
        due_date=None,
        owners=[Participant(alias="owner1", email=EmailAddress(
            email="owner1@example.com", name="Owner One", domain="example.com"))],
        waiters=[Participant(alias="waiter1", email=EmailAddress(
            email="waiter1@example.com", name="Waiter One", domain="example.com"))],
        metadata={"key": "value"},
        confidence_score=0.9,
        message_id="test_message_id",
        id=1
    )
    actionable_item = (email_content, [action_item])
    im.create_tasks(actionable_item)
