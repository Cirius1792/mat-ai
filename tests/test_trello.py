from typing import List
from unittest import TestCase

from matai_v2.trello import Board, ListCard
class MockTrelloClient: 
    # Complete the implementation fo this mocked thrello client that will just answer invocation with stubs AI!
    def authorize(self, return_url: str) -> str:
        return "https://mock-trello.com/authorize"

    def boards(self) -> List[Board]:
        return [
            Board(id="1", name="Test Board 1", url="https://mock-trello.com/board/1"),
            Board(id="2", name="Test Board 2", url="https://mock-trello.com/board/2"),
        ]

    def create_card(self, list_id: str,
                    name: str,
                    desc: str,
                    due: Optional[datetime] = None) -> ListCard:
        pass


class TestTrelloManager(TestCase):
    pass

