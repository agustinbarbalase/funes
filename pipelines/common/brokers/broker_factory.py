import logging
import os
from typing import Type, TypeVar

from common.brokers.messaging import MessageBroker
from common.brokers.rabbitmq import RabbitMQBroker

T = TypeVar("T")


def get_broker(
    model: Type[T], heartbeat: int = 300, logger: logging.Logger | None = None
) -> MessageBroker[T]:
    backend = os.getenv("BROKER_BACKEND", "rabbitmq")
    if backend == "rabbitmq":
        return RabbitMQBroker(
            url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
            model=model,
            heartbeat=heartbeat,
            logger=logger,
        )
    raise ValueError(f"Broker desconocido: {backend}")
