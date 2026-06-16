import logging
import os
import signal
import sys

sys.path.insert(0, "/app")

from common.brokers.broker_factory import get_broker
from common.brokers.messaging import Message
from common.models import Ephemeris, ValidEphemeris

QUEUE_IN = os.getenv("QUEUE_IN", "ephemerides")
QUEUE_OUT = os.getenv("QUEUE_OUT", "valid_ephemerides")

VALID_TYPES = {"Nacimiento", "Fallecimiento", "Evento"}
MIN_TITLE_LEN = 10
MAX_TITLE_LEN = 500
MAX_DESCRIPTION_LEN = 5000


def sanitize_text(text: str) -> str:
    return " ".join(text.split()).strip()


class ValidateWorker:
    def __init__(self, logger):
        self.broker_in = get_broker(Ephemeris, logger=logger)
        self.broker_out = get_broker(ValidEphemeris, logger=logger)
        self.logger = logger
        self._shutdown = False

        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self.logger.info(
            "Señal de terminación recibida, finalizando tras el mensaje actual..."
        )
        self._shutdown = True

    def validate(self, e: Ephemeris) -> tuple[bool, str]:
        title = sanitize_text(e.title)
        if not title:
            return False, "título vacío"
        if len(title) < MIN_TITLE_LEN:
            return False, f"título demasiado corto: {title!r}"
        if len(title) > MAX_TITLE_LEN:
            return False, f"título demasiado largo ({len(title)} chars)"

        if e.type not in VALID_TYPES:
            return False, f"tipo inválido: {e.type!r}"

        if not e.date:
            return False, "fecha vacía"

        return True, "ok"

    def callback(self, msg: Message[Ephemeris]):
        e = msg.body
        ok, reason = self.validate(e)
        if not ok:
            self.logger.warning(f"✗ Descartado [{reason}]: {e.title[:60]}")
            self.broker_in.ack(msg.seq)
            if self._shutdown:
                self._close_and_exit()
            return

        description = sanitize_text(e.description)
        if len(description) > MAX_DESCRIPTION_LEN:
            description = description[:MAX_DESCRIPTION_LEN] + "…"

        images = [url for url in e.images if url.startswith("https://")]
        urls = [url for url in e.urls if url.startswith("https://")]

        valid = ValidEphemeris(
            day=e.day,
            month=e.month,
            year=e.year,
            date=e.date,
            type=e.type,
            title=sanitize_text(e.title),
            description=description,
            images=images,
            urls=urls,
        )
        self.broker_out.publish(QUEUE_OUT, valid)
        self.logger.debug(f"✓ Válida: {valid.title[:60]}")
        self.broker_in.ack(msg.seq)

        if self._shutdown:
            self._close_and_exit()

    def _close_and_exit(self):
        self.logger.info("Cerrando conexiones y saliendo...")
        self.broker_in.close()
        sys.exit(0)

    def run(self):
        self.broker_in.consume(QUEUE_IN, self.callback)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [validate] %(message)s")
    logger = logging.getLogger(__name__)

    validate_worker = ValidateWorker(logger)
    validate_worker.run()
