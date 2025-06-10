from typing import List, Optional, Tuple, Optional, Iterator
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from matai.common.logging import configure_logging
from matai.dao.interface import ActionItemDAO, EmailContentDAO, ParticipantDAO
from matai.email_client.interface import EmailClientInterface
from matai.email_processing.model import ActionItem, EmailContent, Participant
from matai.email_processing.processor import EmailProcessor
from matai.manager.models import RunConfiguration

configure_logging()
logger = logging.getLogger(__name__)


@dataclass
class EmailFilters:
    recipients: List[str]


ActionableEmails = Tuple[EmailContent, List[ActionItem]]
ManagedEmails = Iterator[ActionableEmails] | List[ActionableEmails]


class EmailManager:
    def __init__(self, email_client: EmailClientInterface,
                 action_item_dao: ActionItemDAO,
                 email_content_dao: EmailContentDAO,
                 email_processor: EmailProcessor,
                 participant_dao: ParticipantDAO):
        self._email_client = email_client
        self._action_item_dao = action_item_dao
        self._email_content_dao = email_content_dao
        self._email_processor = email_processor
        self._participant_dao = participant_dao

    def _apply_filters(self, emails: List[EmailContent] | Iterator[EmailContent], filters: EmailFilters) -> List[EmailContent]:
        def get_recipient_email(recipient):
            return recipient.email if hasattr(recipient, "email") else recipient
        if not filters.recipients:
            return list(emails)
        return [email for email in emails if any(get_recipient_email(recipient) in filters.recipients for recipient in email.recipients)]


    def process_new_emails(self, last_run_details: RunConfiguration, filters:Optional[EmailFilters]=None) -> ManagedEmails:
        """
        Process new emails since the last run and return a list of managed emails.

        This method retrieves emails from the email client that have been received since the last run time.
        It filters out emails that have already been processed and stored in the database.
        The remaining new emails are processed to extract action items.

        Args:
            last_run_details: Configuration containing the last run time.

        Returns:
            A list of tuples, each containing an EmailContent object and a list of associated ActionItems.
        """
        # retrieve last run info
        datetime_filter = last_run_details.last_run_time
        if datetime_filter == None:
            # if no last run info, retrieve all emails older than one week
            datetime_filter = datetime.now() - timedelta(days=2)

        logger.info(f"Retrieving emails since {datetime_filter}...")

        # retrieve emails since last run
        emails_to_be_processed = list(self._email_client.read_messages(
            datetime_filter))
        logger.info(f"Retrieving emails since {datetime_filter}... Retrieved {len(emails_to_be_processed)} emails")

        # apply filters if provided
        if filters:
            emails_to_be_processed = self._apply_filters(
                emails_to_be_processed, filters)
            logger.info(f"Filtered emails: {len(emails_to_be_processed)} emails")

        # retrieve stored emails from last run
        already_processed_emails = self._email_content_dao.list_email_contents(
            datetime_filter)

        # filter the retrieved emails to remove the already stored one
        processed_message_ids = {
            email.message_id for email in already_processed_emails}
        new_emails = [
            email for email in emails_to_be_processed if email.message_id not in processed_message_ids]
        logger.info(f"New Emails to be processed: {len(new_emails)}")

        # process the new emails
        for email in new_emails:
            logger.info(
                f"Processing email id {email.message_id} having Subject:{email.subject}")
            action_items = self._email_processor.process_email(email)
            logger.info(f"Extracted action items: {len(action_items)}")
            yield ((email, action_items))

        return None

    def _store_new_paticipants(self, participants: List[Participant]):
        for participant in participants:
            if not self._participant_dao.get_participant(participant.alias):
                self._participant_dao.create_participant(participant)

    def store_processed_emails(self, managed_emails: ManagedEmails) -> ManagedEmails:
        """Store processed emails and their action items in the database.
        
        This method stores both the email content and extracted action items that meet
        the confidence threshold. It also stores any new participants (owners/waiters)
        associated with the action items.
        
        Args:
            managed_emails: List of tuples containing (EmailContent, List[ActionItem])
            confidence_treshold: Minimum confidence score for storing action items
            
        Returns:
            ManagedEmails: The input managed_emails list, unmodified
            
        Note:
            Only action items with confidence scores above the threshold are stored.
            New participants are automatically added to the participant database.
        """
        for email, action_items in managed_emails:
            self._email_content_dao.create_email_content(email)
            for action_item in action_items:
                self._action_item_dao.create_action_item(action_item)
                self._store_new_paticipants(
                    action_item.owners + action_item.waiters)
        return managed_emails
