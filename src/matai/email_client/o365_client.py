from datetime import datetime
from typing import Iterator, Tuple, Optional, List
from O365 import Account

import logging

from matai.email_client.interface import EmailClientInterface
from matai.email_processing.model import EmailContent, EmailAddress

logger = logging.getLogger(__name__)


def consent_input_token(consent_url):
    print('Visit the following url to give consent:')
    print(consent_url)

    return input('Paste the authenticated url here:\n')


DEFAULT_SCOPES = ['mailbox', 'mailbox_shared']


class O365Account:

    def __init__(self, credentials: Tuple[str, str], tenant_id: str, scopes: List[str] = DEFAULT_SCOPES):
        self.account = Account(credentials, tenant_id=tenant_id)
        self.scopes = scopes

    def get_auth_link(self):
        assert self.account.con.auth_flow_type in ('authorization', 'public')
        if self.scopes is not None:
            if self.account.con.scopes is not None:
                raise RuntimeError('The scopes must be set either at the Account '
                                   'instantiation or on the account.authenticate method.')
            self.account.con.scopes = self.account.protocol.get_scopes_for(
                self.scopes)
        else:
            if self.account.con.scopes is None:
                raise ValueError(
                    'The scopes are not set. Define the scopes requested.')

        consent_url, flow = self.account.con.get_authorization_url()
        return (consent_url, flow)

    def complete_authentication(self, token_url, **kwargs):
        # TODO: use the flow object to handle the session properly
        if token_url:
            # no need to pass state as the session is the same
            result = self.account.con.request_token(token_url, **kwargs)
            if result:
                logger.debug(
                    'Authentication Flow Completed. Oauth Access Token Stored. You can now use the API.')
            else:
                logger.debug('Something went wrong')

            return bool(result)
        else:
            logger.warning('Authentication Flow aborted.')
            return False

    @property
    def is_authenticated(self):
        return self.account.is_authenticated


class O365EmailClient(EmailClientInterface):
    """O365-specific implementation of email client interface"""

    def __init__(self, authentication_client: O365Account):
        """
        Initialize O365 client 

        Args:
            authentication_client: O365Account: handles the authenthication with the O365 APIs
        """
        self.client = authentication_client

    def authenticated(self) -> bool:
        """Return True if the client is authenticated"""
        return self.client.is_authenticated

    def read_messages(self, start_date: Optional[datetime] = None, limit: int = 100, **kwargs) -> Iterator[EmailContent]:
        """Read messages and convert to EmailContent objects"""
        if not self.authenticated():
            raise RuntimeError("Authentication failed")

        account = self.client.account
        mailbox = account.mailbox()

        # Create query to filter by date if start_date is provided
        query = None
        if start_date:
            query = mailbox.new_query(
                'received_date_time').greater_equal(start_date)

        # Get messages with pagination, requesting in batches of 100
        messages = mailbox.get_messages(query=query, batch=100, limit=limit)

        # Iterate through all pages of messages
        for msg in messages:  # messages is a Pagination object that handles fetching next pages
            try:
                # Convert sender to EmailAddress
                sender = EmailAddress.from_string(
                    f"{msg.sender.name} <{msg.sender.address}>")

                # Convert recipients to EmailAddress objects
                recipients = []
                for recipient in msg.to:
                    recipients.append(EmailAddress.from_string(
                        f"{recipient.name} <{recipient.address}>"))

                # Create EmailContent object
                content = EmailContent(
                    message_id=msg.object_id,  # O365-specific unique message ID
                    subject=msg.subject,
                    sender=sender,
                    recipients=recipients,
                    thread_id=msg.conversation_id,
                    timestamp=msg.received or datetime.now(),
                    raw_content=str(msg)
                )
                content.body = msg.body  # This will trigger clean_body generation
                logger.debug(
                    f"Retrieved message ID={content.message_id}, subject={content.subject}, received={content.timestamp}")

                yield content
            except: 
                logger.error(f"Error parsing email having object: {msg.subject}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv("email.env")
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    tenant_id = os.getenv('TENANT_ID')
    scopes = ['mailbox', 'mailbox_shared']
    # Assert that all the required environment variables are set and not None.
    assert client_id, "CLIENT_ID is not set"
    assert client_secret, "CLIENT_SECRET is not set"
    assert tenant_id, "TENANT_ID is not set"

    client = O365Account((client_id, client_secret), tenant_id, scopes)
    callback_url, flow = client.get_auth_link()
    print(callback_url)
    returned_url = input("Paste the returned url: ")
    client.complete_authentication(returned_url)
    print(f"is_authenticated: {client.is_authenticated}")
