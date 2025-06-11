from datetime import datetime
from typing import List, Optional
from openai import OpenAI
from datetime import datetime
from string import Template
import json
import logging

from matai.email_processing.model import ActionItem, ActionType, EmailContent, Participant


logger = logging.getLogger(__name__)

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
      "owners": ["person responsible"],
      "waiters": ["person waiting for completion"],
      "project": "project context if mentioned",
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
      "owners": ["team"],
      "waiters": [],
      "project": "Q3 reporting",
      "priority": "medium",
      "confidence": 0.8
    },
    {
      "type": "task",
      "description": "Submit financial data",
      "due_date": "2025-05-28",
      "owners": ["John"],
      "waiters": [],
      "project": "Q3 reporting",
      "priority": "medium",
      "confidence": 0.9
    }
  ]
}
```"""


class EmailProcessor:
    def __init__(self, client: OpenAI, model: str, confidence_threshold: float = 0.85):
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

    def _parse_participants(self, raw) -> List[Participant]:
        """
        Parse a comma-separated string or list of aliases and return a list of Participants with the given role.
        """
        if not raw:
            return []
        if isinstance(raw, list):
            aliases = raw
        else:
            aliases = [alias.strip()
                       for alias in raw.split(",") if alias.strip()]
        return [Participant(alias=alias, email=None) for alias in aliases]

    def _prompt_builder(self, email_content: EmailContent) -> str:
        from_ = ", ".join([e.to_string() for e in email_content.recipients])
        return self._promtp_template.substitute(
            sender=email_content.sender.to_string(),
            recipients=from_,
            subject=email_content.subject,
            email_date=email_content.timestamp.strftime("%y-%m-%d"),
            email_content=email_content.clean_body,
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
            owners=self._parse_participants(
                item_json.get("owners", "")),
            waiters=self._parse_participants(item_json.get(
                "waiters", "")),
            metadata={},
            confidence_score=float(item_json.get("confidence", 0)),
            message_id=message_id
        )

    def process_email(self, email_content: EmailContent, max_retries=3) -> List[ActionItem]:
        """
        Process an email and extract action items.

        Args:
            email_content: Structured email content including body, subject, and metadata

        Returns:
            List of extracted action items with confidence scores
        """

        start_time = datetime.now()
        prompt = self._prompt_builder(email_content)
        logger.debug("Formatted prompt: %s", prompt)
        # Call the LLM to generate a response

        for i in range(max_retries+1):
            try:
                response = self._client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self._model,
                    temperature=0.0,
                    # Request JSON format
                    response_format={"type": "json_object"}
                )

                action_items = []
                logger.info(
                    f"LLM Response: {response.choices[0].message.content}")
                llm_data = json.loads(response.choices[0].message.content)
                for item_json in llm_data.get("action_items", []):
                    due_date = None
                    due_date = self._parse_date(item_json.get("due_date"))
                    due_date = self._sanitarize_date(
                        due_date, email_content.timestamp)
                    action_items.append(
                        self.map_action(
                            due_date, email_content.message_id, item_json)
                    )
                # If I am down here it means the the llm response was ok
                break
            except Exception as e:
                # But if I get here max_attempts times it meas that the computation is failed too many time
                if i == max_retries:
                    logger.error(
                        f"LLM processing failed {max_retries} times with error: {e}")
                    raise e

        processing_time = datetime.now() - start_time
        minutes = processing_time.seconds // 60
        seconds = processing_time.seconds % 60
        logger.info(
            f"Processed email {email_content.message_id} in {minutes}m {seconds}s")

        return action_items
