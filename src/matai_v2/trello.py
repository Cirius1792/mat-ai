import logging
from datetime import datetime
from typing import List, Optional
import requests
from dataclasses import dataclass
from urllib.parse import urlencode

from matai_v2.processor import ActionItem


@dataclass
class BoardList:
    id: str
    name: str
    idBoard: str


@dataclass
class TrelloAttachments:
    board: int
    card: int


@dataclass
class AttachmentsByType:
    trello: TrelloAttachments


@dataclass
class Badges:
    attachmentsByType: AttachmentsByType
    location: bool
    votes: int
    viewingMemberVoted: bool
    subscribed: bool
    fogbugz: str
    checkItems: int
    checkItemsChecked: int
    comments: int
    attachments: int
    description: bool
    due: str
    start: str
    dueComplete: bool


@dataclass
class ListCard:
    id: str
    address: str
    badges: Badges
    desc: str
    due: str
    idBoard: str
    idList: str
    idMembers: list
    idShort: int
    name: str
    pos: int
    shortLink: str
    shortUrl: str
    subscribed: bool
    url: str


@dataclass
class Board:
    id: str
    name: str
    url: str


logger = logging.getLogger(__name__)


class TrelloClient:
    # This is the original client for which we want to build a test double. Take into consideration the actual dataclass and do not fuck up with the object initialization AI
    AUTH_URL = "https://trello.com/1/authorize?"
    BASE_URL = "https://api.trello.com/1"

    def __init__(self, api_key: str, api_token: Optional[str] = None):
        self.api_key = api_key
        self._token = api_token

    def authorize(self, return_url: str) -> str:
        """Returns the url to authorize the app
        Args:
            return_url (str): The url to redirect the user after the authorization
        Returns:
            str: The url where the client will follow the authorization path
            """

        params = {
            "expiration": "never",
            "return_url": return_url,
            "name": "NewToken",
            "scope": "read,write,account",
            "response_type": "token",
            "key": self.api_key,
        }
        return self.AUTH_URL + urlencode(params)

    @property
    def token(self) -> Optional[str]:
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value

    def boards(self) -> List[Board]:
        """Returns the list of the boards that belong to the user
        Returns:
            List[Board]: List of boards
        """
        logger.info("Fetching boards")
        url = f"{self.BASE_URL}/members/me/boards?fields=name,url&key={self.api_key}&token={self._token}"
        response = requests.get(url)
        if not response.ok:
            raise Exception(
                f"Failed to fetch boards: {response.status_code} {response.text}")
        boards_json = response.json()
        return [Board(id=board["id"], name=board["name"], url=board["url"]) for board in boards_json]

    def map_list(self, board_list) -> BoardList:
        return BoardList(id=board_list["id"], name=board_list["name"], idBoard=board_list["idBoard"])

    def lists(self, board_id: str) -> List[BoardList]:
        """Returns the list of the lists that belong to the board with the given id
        Args:
            board_id (str): The board id
        Returns:
            List[BoardList]: List of lists
                    """

        headers = {
            "Accept": "application/json"
        }

        query = {
            'key': self.api_key,
            'token': self.token
        }
        url = f"{self.BASE_URL}/boards/{board_id}/lists"
        response = requests.request(
            "GET",
            url,
            headers=headers,
            params=query
        )
        if not response.ok:
            raise Exception(
                f"Failed to fetch lists: {response.status_code} {response.text}")
        lists_json = response.json()
        return [self.map_list(board_list) for board_list in lists_json]

    def create_list(self, board_id: str, list_name: str) -> BoardList:
        """Creates a new list in the board with the given id
        Args:
            board_id (str): The board id
            list_name (str): The name of the list
        Returns:
            BoardList: The created list
                    """
        url = f"{self.BASE_URL}/boards/{board_id}/lists"

        headers = {
            "Accept": "application/json"
        }

        query = {
            'name': list_name,
            'key': self.api_key,
            'token': self.token
        }

        response = requests.request(
            "POST",
            url,
            headers=headers,
            params=query
        )
        if not response.ok:
            raise Exception(
                f"Failed to create list: {response.status_code} {response.text}")

        response_json = response.json()

        return self.map_list(response_json)

    def create_card(self, list_id: str,
                    name: str,
                    desc: str,
                    due: Optional[datetime] = None) -> ListCard:
        """
        Creates a new card in the specified list.
        Args:
            list_id (str): The ID of the list.
            name (str): The name of the card.
            desc (str): The description of the card.
            due (Optional[str]): The due date. Defaults to None.
        Returns:
            ListCard: The created card, mapped from the Trello API response.
        """
        url = f"{self.BASE_URL}/cards"

        headers = {
            "Accept": "application/json"
        }

        body = {
            'idList': list_id,
            'key': self.api_key,
            'token': self.token,
            'name': name,
            'desc': desc,
            'due': due,
        }

        response = requests.request(
            "POST",
            url,
            headers=headers,
            data=body
        )
        if not response.ok:
            raise Exception(
                f"Failed to create card: {response.status_code} {response.text}")
        response_json = response.json()
        return self.map_card(response_json)

    def map_card(self, response_json) -> ListCard:
        badges_obj = response_json.get("badges", {})
        attachments_by_type = badges_obj.get("attachmentsByType", {})
        trello_info = attachments_by_type.get("trello", {})
        attachments = TrelloAttachments(
            board=trello_info.get("board", 0),
            card=trello_info.get("card", 0)
        )
        attachments_by_type_obj = AttachmentsByType(
            trello=attachments
        )
        badges = Badges(
            attachmentsByType=attachments_by_type_obj,
            location=badges_obj.get("location", False),
            votes=badges_obj.get("votes", 0),
            viewingMemberVoted=badges_obj.get("viewingMemberVoted", False),
            subscribed=badges_obj.get("subscribed", False),
            fogbugz=badges_obj.get("fogbugz", ""),
            checkItems=badges_obj.get("checkItems", 0),
            checkItemsChecked=badges_obj.get("checkItemsChecked", 0),
            comments=badges_obj.get("comments", 0),
            attachments=badges_obj.get("attachments", 0),
            description=badges_obj.get("description", False),
            due=badges_obj.get("due", ""),
            start=badges_obj.get("start", ""),
            dueComplete=badges_obj.get("dueComplete", False)
        )
        return ListCard(
            id=response_json.get("id", ""),
            address=response_json.get("address", ""),
            badges=badges,
            desc=response_json.get("desc", ""),
            due=response_json.get("due", ""),
            idBoard=response_json.get("idBoard", ""),
            idList=response_json.get("idList", ""),
            idMembers=response_json.get("idMembers", []),
            idShort=response_json.get("idShort", 0),
            name=response_json.get("name", ""),
            pos=response_json.get("pos", 0),
            shortLink=response_json.get("shortLink", ""),
            shortUrl=response_json.get("shortUrl", ""),
            subscribed=response_json.get("subscribed", False),
            url=response_json.get("url", "")
        )


logger = logging.getLogger(__name__)


class TrelloBoardManager:
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

    def _create_card_description(self, subject: str, body: str) -> str:
        return f"Thread Subject: {subject}\nOriginal Message: \n{body}"

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
        return f"{str(action_item.action_type)}: {action_item.description}"

    def create_tasks(self,
                        subject: str,
                        body: str,
                        action_items: List[ActionItem]):
        if self.list_id is None:
            self.setup()

        assert self.list_id is not None, "List ID must be set before creating tasks"
        for action_item in action_items:
            description = self._create_card_description(
                subject, body)
            name = self._create_card_name(action_item)
            due_date = action_item.due_date if action_item.due_date else None
            logger.info("Creating card in list %s with name %s",
                        self._app_board, name)
            logger.info("Card description: %s", description)
            card = self._client.create_card(
                self.list_id, name, description, due_date)
            logger.info("Created card %s in list %s",
                        card.name, self._app_board)
