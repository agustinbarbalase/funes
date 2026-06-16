import logging
import os
import re
import signal
import sys

sys.path.insert(0, "/app")

from common.brokers.broker_factory import get_broker
from common.brokers.messaging import Message
from common.models import RawPage, Ephemeris

QUEUE_IN = os.getenv("QUEUE_IN", "raw_pages")
QUEUE_OUT = os.getenv("QUEUE_OUT", "ephemerides")

TYPE_MAP = {
    "births": "Nacimiento",
    "deaths": "Fallecimiento",
    "events": "Evento",
}

MAX_PER_TYPE = {
    "Nacimiento": 20,
    "Fallecimiento": 30,
    "Evento": 50,
}

SKIP_IMAGE_PATTERNS = [
    "Flag_of",
    "coat_of_arms",
    "Coat_of",
    ".svg",
    "icon",
    "Icon",
    "Avenida",
    "panoram",
    "Plaza",
    "mapa",
    "Mapa",
    "locator",
    "Locator",
    "location",
    "Location",
    "map",
    "Map",
]

SKIP_DESCRIPTIONS = {"fecha", "año", "siglo", "milenio", "década"}

DATE_PAGE_RE = re.compile(
    r"^\d{1,2}\s+de\s+\w+$|"
    r"^\w+\s+de\s+\d{4}$|"
    r"^\d{4}$|"
    r"^Anexo:|^Wikipedia:|^Portal:",
    re.IGNORECASE,
)


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def filter_image(url: str) -> bool:
    if not url:
        return False
    return not any(p in url for p in SKIP_IMAGE_PATTERNS)


def is_valid_page(page: dict) -> bool:
    description = page.get("description", "").lower().strip()
    if description in SKIP_DESCRIPTIONS:
        return False
    title = page.get("normalizedtitle") or page.get("title", "")
    if DATE_PAGE_RE.search(title):
        return False
    return True


class TransformWorker:
    def __init__(self, logger):
        self.broker_in = get_broker(RawPage, logger=logger)
        self.broker_out = get_broker(Ephemeris, logger=logger)
        self.logger = logger
        self._shutdown = False

        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self.logger.info(
            "Señal de terminación recibida, finalizando tras el mensaje actual..."
        )
        self._shutdown = True

    def transform(self, day: int, month: int, data: dict) -> list[Ephemeris]:
        seen_texts = set()
        results_by_type: dict[str, list[Ephemeris]] = {t: [] for t in MAX_PER_TYPE}

        for section, tipo in TYPE_MAP.items():
            for entry in data.get(section, []):
                if len(results_by_type[tipo]) >= MAX_PER_TYPE[tipo]:
                    continue

                year = entry.get("year")
                date_str = (
                    f"{day:02d}/{month:02d}/{year}"
                    if year
                    else f"{day:02d}/{month:02d}"
                )
                event_text = strip_html(entry.get("text", ""))
                if not event_text or event_text in seen_texts:
                    continue
                seen_texts.add(event_text)

                pages = entry.get("pages", [])
                main_page = next((p for p in pages if is_valid_page(p)), None)

                description = ""
                wiki_url = ""
                if main_page:
                    description = (
                        main_page.get("extract") or main_page.get("description") or ""
                    )
                    wiki_url = (
                        main_page.get("content_urls", {})
                        .get("desktop", {})
                        .get("page", "")
                    )

                images = []
                for page in pages:
                    if not is_valid_page(page):
                        continue
                    original = page.get("originalimage", {})
                    thumbnail = page.get("thumbnail", {})
                    for src in [
                        original.get("source", ""),
                        thumbnail.get("source", ""),
                    ]:
                        if filter_image(src) and src not in images:
                            images.append(src)
                            break
                    if len(images) >= 5:
                        break

                results_by_type[tipo].append(
                    Ephemeris(
                        day=day,
                        month=month,
                        year=year,
                        date=date_str,
                        type=tipo,
                        title=event_text,
                        description=description,
                        images=images,
                        urls=[wiki_url] if wiki_url else [],
                    )
                )

        results = (
            results_by_type["Evento"]
            + results_by_type["Fallecimiento"]
            + results_by_type["Nacimiento"]
        )
        self.logger.info(
            f"  {day}/{month}: {len(results)} efemérides "
            f"(E:{len(results_by_type['Evento'])} "
            f"F:{len(results_by_type['Fallecimiento'])} "
            f"N:{len(results_by_type['Nacimiento'])})"
        )
        return results

    def callback(self, msg: Message[RawPage]):
        day, month = msg.body.day, msg.body.month
        ephemerides = self.transform(day, month, msg.body.data)
        for e in ephemerides:
            self.broker_out.publish(QUEUE_OUT, e)
        self.broker_in.ack(msg.seq)

        if self._shutdown:
            self.logger.info("Cerrando conexiones y saliendo...")
            self.broker_in.close()
            sys.exit(0)

    def run(self):
        self.broker_in.consume(QUEUE_IN, self.callback)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [transform] %(message)s"
    )
    logger = logging.getLogger(__name__)

    transform_worker = TransformWorker(logger)
    transform_worker.run()
