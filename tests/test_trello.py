from typing import List, Optional
from datetime import datetime
from unittest import TestCase

from matai_v2.trello import (
    Board,
    BoardList,
    ListCard,
    Badges,
    AttachmentsByType,
    TrelloAttachments,
    TrelloBoardManager,
)
from matai_v2.processor import ActionItem, ActionType


class MockTrelloClient:
    """Simple in-memory stub of the TrelloClient API surface used by TrelloBoardManager."""

    def __init__(self):
        self.created_lists: List[BoardList] = []
        self.created_cards: List[ListCard] = []
        # Pre-populate board '1' with a single list not named 'Mantis'
        self._lists_by_board = {
            "1": [BoardList(id="l1", name="Todo", idBoard="1")],
            "2": [],
        }

    def authorize(self, return_url: str) -> str:  # noqa: D401  (docstring ignored for stub)
        return "https://mock-trello.com/authorize"

    def boards(self) -> List[Board]:
        return [
            Board(id="1", name="Test Board 1", url="https://mock-trello.com/board/1"),
            Board(id="2", name="Test Board 2", url="https://mock-trello.com/board/2"),
        ]

    # ---------- List helpers -------------------------------------------------
    def lists(self, board_id: str) -> List[BoardList]:
        return self._lists_by_board.get(board_id, [])

    def create_list(self, board_id: str, list_name: str) -> BoardList:
        new_list = BoardList(id=f"new_{len(self.created_lists)}", name=list_name, idBoard=board_id)
        self.created_lists.append(new_list)
        self._lists_by_board.setdefault(board_id, []).append(new_list)
        return new_list

    # ---------- Card helpers -------------------------------------------------
    def _empty_badges(self) -> Badges:
        """Return a minimal Badges object so we don’t have to repeat the boilerplate."""
        return Badges(
            attachmentsByType=AttachmentsByType(
                trello=TrelloAttachments(board=0, card=0)
            ),
            location=False,
            votes=0,
            viewingMemberVoted=False,
            subscribed=False,
            fogbugz="",
            checkItems=0,
            checkItemsChecked=0,
            comments=0,
            attachments=0,
            description=False,
            due="",
            start="",
            dueComplete=False,
        )

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str,
        due: Optional[datetime] = None,
    ) -> ListCard:
        """Return a stubbed ListCard and remember it for assertions."""
        card = ListCard(
            id=f"c_{len(self.created_cards)}",
            address="",
            badges=self._empty_badges(),
            desc=desc,
            due=due.isoformat() if isinstance(due, datetime) else "",
            idBoard="1",
            idList=list_id,
            idMembers=[],
            idShort=len(self.created_cards),
            name=name,
            pos=0,
            shortLink="",
            shortUrl="",
            subscribed=False,
            url="",
        )
        self.created_cards.append(card)
        return card


# --------------------------------------------------------------------------- #
#                                Test-suite                                   #
# --------------------------------------------------------------------------- #
class TestTrelloManager(TestCase):
    def setUp(self):
        self.mock_client = MockTrelloClient()
        self.manager = TrelloBoardManager(self.mock_client, board_id="1")

    def test_setup_creates_mantis_list(self):
        """setup() should create a 'Mantis' list if absent and store its ID."""
        self.manager.setup()
        self.assertIsNotNone(self.manager.list_id)
        self.assertIn("Mantis", [lst.name for lst in self.mock_client.created_lists])

    def test_create_tasks_creates_cards(self):
        """create_tasks() should result in a new card on the mock client."""
        self.manager.setup()
        action_item = ActionItem(
            action_type=ActionType.TASK,
            description="Demo task",
            confidence_score=0.9,
            message_id="msg-1",
            due_date=datetime(2025, 1, 1),
            id=1,
        )
        self.manager.create_tasks(
            subject="Subject line",
            body="Body content",
            action_items=[action_item],
        )
        self.assertEqual(len(self.mock_client.created_cards), 1)
        created_card = self.mock_client.created_cards[0]
        expected_name = f"{str(action_item.action_type)}: {action_item.description}"
        self.assertEqual(created_card.name, expected_name)

