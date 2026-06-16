import json
import logging
import os
import pathlib
import signal
import sys
import time

import requests
from requests.exceptions import HTTPError

sys.path.insert(0, "/app")

from common.brokers.broker_factory import get_broker
from common.brokers.messaging import Message
from common.models import Task, RawPage

QUEUE_IN = os.getenv("QUEUE_IN", "tasks")
QUEUE_OUT = os.getenv("QUEUE_OUT", "raw_pages")
WIKIPEDIA_ENDPOINT = os.getenv(
    "WIKIPEDIA_ENDPOINT", "https://es.wikipedia.org/api/rest_v1"
)
CACHE_DIR = pathlib.Path("/app/cache/raw")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "EfemeridesBot/1.0", "Accept": "application/json"}


class FetchWorker:
    def __init__(self, logger):
        self.broker_in = get_broker(Task, logger=logger)
        self.broker_out = get_broker(RawPage, logger=logger)
        self.logger = logger
        self._shutdown = False

        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self.logger.info(
            "Señal de terminación recibida, finalizando tras el mensaje actual..."
        )
        self._shutdown = True

    def fetch_wikipedia(self, day: int, month: int) -> dict | None:
        cache_file = CACHE_DIR / f"{month:02d}-{day:02d}.json"
        if cache_file.exists():
            self.logger.info(f"  Cache hit: {cache_file}")
            return json.loads(cache_file.read_text(encoding="utf-8"))

        url = f"{WIKIPEDIA_ENDPOINT}/feed/onthisday/all/{month:02d}/{day:02d}"
        for attempt in range(5):
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                r.raise_for_status()
                data = r.json()
                cache_file.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                total = sum(
                    len(data.get(k, [])) for k in ("births", "deaths", "events")
                )
                self.logger.info(
                    f"  {day}/{month}: {total} resultados → cache guardado"
                )
                return data
            except HTTPError as e:
                if e.response.status_code == 429:
                    wait = 2**attempt
                    self.logger.warning(
                        f"  429 {day}/{month} → esperando {wait}s (intento {attempt+1}/5)"
                    )
                    time.sleep(wait)
                else:
                    self.logger.error(f"✗ Error Wikipedia {day}/{month}: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"✗ Error Wikipedia {day}/{month}: {e}")
                return None
        self.logger.error(f"✗ {day}/{month}: máximo de reintentos alcanzado")
        return None

    def callback(self, msg: Message[Task]):
        day, month = msg.body.day, msg.body.month
        self.logger.info(f"Procesando: {day}/{month}")
        data = self.fetch_wikipedia(day, month)
        if data:
            self.broker_out.publish(QUEUE_OUT, RawPage(day=day, month=month, data=data))
        self.broker_in.ack(msg.seq)

        if self._shutdown:
            self.logger.info("Cerrando conexiones y saliendo...")
            self.broker_in.close()
            sys.exit(0)

    def run(self):
        self.broker_in.consume(QUEUE_IN, self.callback)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [fetch] %(message)s")
    logger = logging.getLogger(__name__)

    fetch_worker = FetchWorker(logger)
    fetch_worker.run()
