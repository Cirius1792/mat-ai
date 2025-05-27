import json
import os
from datetime import datetime, timedelta
from src.pmai.email_client.o365_client import O365EmailClient
import logging
from dotenv import load_dotenv
from matai.common.logging import configure_logging
configure_logging()


logger = logging.getLogger(__name__)


def main():
    load_dotenv("email.env")
    credentials = (os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
    tenant_id = os.getenv("TENANT_ID")

    client = O365EmailClient(credentials, tenant_id)
    # add a start date to filter messages parsing it from a string
    start_date = datetime.now() - timedelta(days=7)
    messages = client.read_messages(start_date=start_date, limit=25)
    messages = list(messages)
    logger.info(len(messages))
    with open("message_dump.json", "w") as f:
        json.dump([m.to_json() for m in messages], f, indent=2)
    for message in messages:
        logger.info(message)

        # print(message.clean_body)


if __name__ == "__main__":
    main()
