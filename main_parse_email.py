from openai import OpenAI
from matai.common.logging import configure_logging
from matai.email_processing.model import EmailContent, EmailAddress
from datetime import datetime

from matai.email_processing.processor import EmailProcessor
from tests.email_processing.test_processor import processor
import logging
configure_logging()
logger = logging.getLogger(__name__)


SAMPLE_EMAIL = """Ciao a tutti,

 

blocco questo slot per definire la data preparation e l’esecuzione dei system test degli “Eventi di struttura”.

Durante la call è richiesto il contributo di:

GT
CJ Piani
CDM
Valore insieme
CJ Conti correnti
 

Pertanto vi chiedo gentilmente di rispondere alla seguente convocazione indicando se riuscirete a partecipare nello slot indicato entro domani 06/02.

Qualora non foste disponibili vi chiedo di indicarmi degli slot alternativi in cui siete disponibili oppure i colleghi che vi potranno sostituire partecipando alla call.

 

Vi chiedo inoltre di estendere l’invito ai colleghi qualora lo riteniate necessario.

 

Grazie,

Gianvito

 """

EMAIL = EmailContent(
    message_id="test_1",
    subject="Allineamento su Data Preparation",
    sender=EmailAddress("gianvito@example.com", "Gianvito", "example.com"),
    recipients=[EmailAddress("pippo@example.com", "Pippo", "example.com")],
    thread_id="111",
    timestamp=datetime(2025, 2, 20),
    raw_content=SAMPLE_EMAIL
)


def main():
    processor = EmailProcessor(
        client=OpenAI(), model="gpt-4o", confidence_threshold=0.85)
    action_items = processor.process_email(EMAIL)
    for action_item in action_items:
        logger.info(action_item)


if __name__ == "__main__":
    main()
