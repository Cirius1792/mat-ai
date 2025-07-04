import logging
from datetime import datetime
from typing import List, Optional
import requests
from dataclasses import dataclass
from urllib.parse import urlencode


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
            raise Exception(f"Failed to fetch boards: {response.status_code} {response.text}")
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
            raise Exception(f"Failed to fetch lists: {response.status_code} {response.text}")
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
            raise Exception(f"Failed to create list: {response.status_code} {response.text}")

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
            raise Exception(f"Failed to create card: {response.status_code} {response.text}")
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



