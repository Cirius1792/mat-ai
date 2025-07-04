from datetime import datetime
from typing import List, Optional, Dict
from openai import OpenAI
from datetime import datetime
from string import Template
import json
import logging
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


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
            f"  Confidence: {self.confidence_score}\n"
        )

    def __asdict__(self) -> Dict:
        return self.to_json()

    def to_json(self) -> Dict:
        """Convert action item to JSON serializable format."""
        return {
            "id": self.id,
            "action_type": self.action_type.name,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "confidence_score": self.confidence_score,
            "message_id": self.message_id
        }


def load_action_item_from_json(data: Dict) -> ActionItem:
    """Convert JSON data to ActionItem object."""
    action_type = ActionType.from_string(data.get("action_type", ""))
    description = data.get("description", "")
    confidence_score = data.get("confidence_score", 0.0)
    message_id = data.get("message_id", "")
    due_date_str = data.get("due_date")
    due_date = datetime.fromisoformat(due_date_str) if due_date_str else None
    return ActionItem(
        action_type=action_type,
        description=description,
        confidence_score=confidence_score,
        message_id=message_id,
        due_date=due_date,
    )


class Priority(Enum):
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


EXTRACTION_PROMPT = """You are a specialized task extraction system. Your sole purpose is to identify action items from emails and format them as structured tasks. Analyze the following email:

<email>
From: $sender
To: $recipients
Subject: $subject
Date: $email_date

$email_content
</email>

## TASK EXTRACTION RULES
1. Extract ONLY explicit tasks where:
   - Someone is clearly expected to do something
   - A deadline is mentioned or can be inferred
2. For relative deadlines (tomorrow, next week, in 3 days), calculate the actual date using the email date ($email_date)
3. For incomplete dates (like "March 10" without year), assume the current or next occurrence
4. Use the same language as the email for descriptions
5. Return ONLY the JSON object, no additional text
6. Empty fields use "" for strings, [] for arrays
7. If no valid tasks found, return {"action_items": []}

## OUTPUT FORMAT
Return only a clean JSON object with this structure:
```
{
  "action_items": [
    {
      "type": "task", 
      "description": "Brief, actionable description",
      "due_date": "YYYY-MM-DD[THH:MM:SS]", 
      "priority": "high|medium|low",
      "confidence": 0.0-1.0
    }
  ]
}
```

## PRIORITY GUIDELINES
- HIGH: Urgent terms (ASAP, urgent, today) or executive requests
- MEDIUM: Standard work with clear timelines
- LOW: FYI items or low-pressure requests

## CONFIDENCE SCORING
- 0.9-1.0: Explicit task with clear deadline and owner
- 0.7-0.8: Clear task but some details inferred
- 0.5-0.6: Task exists but significant details missing
- Below 0.5: Potential task but highly uncertain

## EXAMPLE
Email: "Hi team, please complete the Q3 report by next Friday. John needs to submit financial data by Wednesday."

Output:
```json
{
  "action_items": [
    {
      "type": "task",
      "description": "Complete Q3 report",
      "due_date": "2025-05-30",
      "priority": "medium",
      "confidence": 0.8
    },
    {
      "type": "task",
      "description": "Submit financial data",
      "due_date": "2025-05-28",
      "priority": "medium",
      "confidence": 0.9
    }
  ]
}
```"""


class EmailProcessor:
    def __init__(self, client: OpenAI, model: str):
        """
        Initialize the email processor with an LLM service and confidence threshold.

        Args:
            llm_service: Service for LLM interactions
            confidence_threshold: Minimum confidence score for automatic acceptance
        """
        self._client = client
        self._model = model
        self._promtp_template = Template(EXTRACTION_PROMPT)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # Try parsing as a full datetime first
            return datetime.fromisoformat(date_str)
        except ValueError:
            try:
                # Fallback to parsing as a date only
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid date format: {date_str}")
                return None

    def _prompt_builder(self,
                        subject: str,
                        sender: str,
                        recipients: List[str],
                        email_date: datetime,
                        body: str,
                        ) -> str:
        from_ = ", ".join([e for e in recipients])
        return self._promtp_template.substitute(
            sender=sender,
            recipients=from_,
            subject=subject,
            email_date=email_date.strftime("%y-%m-%d"),
            email_content=body,
        )

    def _sanitarize_date(self, due_date: Optional[datetime], email_date: datetime) -> datetime:
        if due_date is None:
            return email_date
        # Convert both datetimes to naive for comparison
        naive_due = due_date.replace(tzinfo=None)
        naive_email = email_date.replace(tzinfo=None)
        if naive_due < naive_email:
            return email_date
        return due_date

    def map_action(self, due_date, message_id, item_json) -> ActionItem:
        return ActionItem(
            action_type=ActionType.from_string(
                item_json.get("type", "task")),
            description=item_json.get("description", ""),
            due_date=due_date,
            confidence_score=float(item_json.get("confidence", 0)),
            message_id=message_id
        )

    def process_email(self, message_id: str,
                      subject: str,
                      sender: str,
                      recipients: List[str],
                      email_date: datetime,
                      body: str,
                      max_retries=3) -> List[ActionItem]:
        """
        Process an email and extract action items.

        Args:
            - message_id: Unique identifier for the email
            - subject: Subject of the email
            - sender: Email address of the sender
            - recipients: List of email addresses of the recipients
            - email_date: Date and time the email was sent
            - body: Body of the email
            - max_retries: Number of retries for LLM processing in case of failure
        Returns:
            List of extracted action items with confidence scores
        """

        start_time = datetime.now()
        prompt = self._prompt_builder(
            subject,
            sender,
            recipients,
            email_date,
            body
        )
        logger.debug("Formatted prompt: %s", prompt)
        # Call the LLM to generate a response
        action_items = self._extract_action_items(
            message_id=message_id,
            prompt=prompt,
            email_date=email_date,
            max_retries=max_retries
        )

        processing_time = datetime.now() - start_time
        minutes = processing_time.seconds // 60
        seconds = processing_time.seconds % 60
        logger.info(
            f"Processed email {message_id} in {minutes}m {seconds}s")

        return action_items

    def _extract_action_items(self, message_id, prompt, email_date, max_retries) -> List[ActionItem]:
        action_items = []
        for attempt in range(max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self._model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    timeout=60  # seconds
                )

                logger.info(
                    f"LLM Response: {response.choices[0].message.content}")
                assert response.choices[0].message.content, "LLM response is empty"
                llm_data = json.loads(response.choices[0].message.content)
                for item_json in llm_data.get("action_items", []):
                    due_date = None
                    due_date = self._parse_date(item_json.get("due_date"))
                    due_date = self._sanitarize_date(
                        due_date, email_date)
                    action_items.append(
                        self.map_action(
                            due_date, message_id, item_json)
                    )
                # If I am down here it means the the llm response was ok
                break
            except Exception as e:
                # But if I get here max_attempts times it meas that the computation is failed too many time
                if attempt == max_retries:
                    logger.error(
                        f"LLM processing failed {max_retries} times with error: {e}")
                    raise e
        return action_items
