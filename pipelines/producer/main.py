import argparse
import datetime
import logging
import os
import sys

sys.path.insert(0, "/app")

from common.brokers.broker_factory import get_broker
from common.models import Task

QUEUE_OUT = os.getenv("QUEUE_OUT", "tasks")

DAYS_PER_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class Producer:
    def __init__(self, logger):
        self.broker = get_broker(Task, logger=logger)
        self.logger = logger

    def emit_all(self):
        total = 0
        for month, days in enumerate(DAYS_PER_MONTH, start=1):
            for day in range(1, days + 1):
                self.broker.publish(QUEUE_OUT, Task(day=day, month=month))
                total += 1
        self.logger.info(f"✓ {total} tareas emitidas")

    def emit_day(self, day: int, month: int):
        self.broker.publish(QUEUE_OUT, Task(day=day, month=month))
        self.logger.info(f"✓ Tarea emitida: {day}/{month}")

    def close(self):
        self.broker.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    producer = Producer(logger)

    if args.all:
        producer.emit_all()
    elif args.day and args.month:
        producer.emit_day(args.day, args.month)
    else:
        today = datetime.date.today()
        producer.emit_day(today.day, today.month)

    producer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [producer] %(message)s")
    logger = logging.getLogger(__name__)
    main()
