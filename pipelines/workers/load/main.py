import logging
import os
import signal
import sys
import time
from collections import defaultdict, deque

import requests
from requests.exceptions import HTTPError

sys.path.insert(0, "/app")

from common.brokers.broker_factory import get_broker
from common.brokers.messaging import Message
from common.models import ValidEphemeris

QUEUE_IN = os.getenv("QUEUE_IN", "valid_ephemerides")
API_URL = os.getenv("API_URL", "http://0.0.0.0:8000")

MIN_BUFFER_SIZE = int(os.getenv("MIN_BUFFER_SIZE", "20"))
MAX_BUFFER_SIZE = int(os.getenv("MAX_BUFFER_SIZE", "400"))
FLUSH_TIMEOUT = float(os.getenv("FLUSH_TIMEOUT", "30"))
RATE_WINDOW = float(os.getenv("RATE_WINDOW", "10"))
HIGH_RATE_THRESHOLD = float(os.getenv("HIGH_RATE_THRESHOLD", "5"))


class LoadWorker:
    def __init__(self, logger: logging.Logger):
        self.broker_in = get_broker(ValidEphemeris, logger=logger)
        self.logger = logger
        self._buffer: dict[tuple, list[dict]] = defaultdict(list)
        self._pending_acks: dict[tuple, list[int]] = defaultdict(list)
        self._buffer_started_at: dict[tuple, float] = {}
        self._arrival_times: deque[float] = deque()
        self._shutdown = False

        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self.logger.info("Señal de terminación recibida, finalizando...")
        self._shutdown = True

    def _record_arrival(self):
        now = time.time()
        self._arrival_times.append(now)
        cutoff = now - RATE_WINDOW
        while self._arrival_times and self._arrival_times[0] < cutoff:
            self._arrival_times.popleft()

    def _current_arrival_rate(self) -> float:
        if len(self._arrival_times) < 2:
            return 0.0
        span = self._arrival_times[-1] - self._arrival_times[0]
        return len(self._arrival_times) / span if span > 0 else 0.0

    def _target_flush_size(self) -> int:
        rate = self._current_arrival_rate()
        ratio = min(rate / HIGH_RATE_THRESHOLD, 1.0)
        return max(
            MIN_BUFFER_SIZE,
            int(MIN_BUFFER_SIZE + ratio * (MAX_BUFFER_SIZE - MIN_BUFFER_SIZE)),
        )

    def ingest(self, day: int, month: int, ephemerides: list[dict]) -> bool:
        url = f"{API_URL}/ingest/{day}/{month}"
        for attempt in range(5):
            try:
                resp = requests.post(
                    url, json={"ephemerides": ephemerides}, timeout=300
                )
                resp.raise_for_status()
                data = resp.json()
                self.logger.info(
                    f"✓ {day}/{month}: inserted={data['inserted']} "
                    f"embedded={data['embedded']} skipped={data['skipped']}"
                )
                return True
            except HTTPError as e:
                if e.response.status_code in (429, 500, 502, 503):
                    wait = 2**attempt
                    self.logger.warning(
                        f"  {e.response.status_code} {day}/{month} → esperando {wait}s (intento {attempt+1}/5)"
                    )
                    time.sleep(wait)
                else:
                    self.logger.error(f"✗ {day}/{month}: {e}")
                    return False
            except requests.RequestException as e:
                self.logger.error(f"✗ {day}/{month}: {e}")
                return False
        self.logger.error(f"✗ {day}/{month}: máximo de reintentos alcanzado")
        return False

    def flush(self, key: tuple):
        day, month = key
        batch = self._buffer.pop(key, [])
        seqs = self._pending_acks.pop(key, [])
        self._buffer_started_at.pop(key, None)

        if not batch:
            return

        if self.ingest(day, month, batch):
            for seq in seqs:
                self.broker_in.ack(seq)
        else:
            for seq in seqs:
                self.broker_in.nack(seq, requeue=True)

    def flush_all(self):
        for key in list(self._buffer.keys()):
            self.logger.info(
                f"Flush: {key[0]}/{key[1]} ({len(self._buffer[key])} msgs)"
            )
            self.flush(key)

    def _flush_timed_out_buffers(self):
        now = time.time()
        for key in list(self._buffer.keys()):
            started = self._buffer_started_at.get(key)
            if started and (now - started) >= FLUSH_TIMEOUT:
                self.logger.info(
                    f"Flush por timeout: {key[0]}/{key[1]} "
                    f"({len(self._buffer[key])} msgs, {now - started:.1f}s)"
                )
                self.flush(key)

    def callback(self, msg: Message[ValidEphemeris]):
        self._record_arrival()

        e = msg.body
        key = (e.day, e.month)

        if key not in self._buffer_started_at:
            self._buffer_started_at[key] = time.time()

        self._buffer[key].append(
            {
                "date": e.date,
                "type": e.type,
                "title": e.title,
                "description": e.description,
                "images": e.images,
                "urls": e.urls,
            }
        )
        self._pending_acks[key].append(msg.seq)

        if len(self._buffer[key]) >= self._target_flush_size():
            self.flush(key)

    def run(self):
        self.broker_in.declare(QUEUE_IN)
        self.broker_in.set_callback(QUEUE_IN, self.callback, prefetch=MAX_BUFFER_SIZE)

        while not self._shutdown:
            self.broker_in.process_events(time_limit=1)
            self._flush_timed_out_buffers()

        self.logger.info("Shutdown: flusheando buffers pendientes...")
        self.flush_all()
        self.broker_in.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [load] %(message)s")
    logger = logging.getLogger(__name__)
    LoadWorker(logger).run()
