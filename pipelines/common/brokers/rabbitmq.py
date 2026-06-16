import dataclasses
import json
import logging
import time
import pika
import pika.exceptions
from typing import Callable, Type, TypeVar

from common.brokers.messaging import MessageBroker, Message

logging.getLogger("pika").disabled = True

T = TypeVar("T")

MAX_RETRIES = 5
RETRY_DELAY = 5


class RabbitMQBroker(MessageBroker[T]):

    def __init__(
        self,
        url: str,
        model: Type[T],
        heartbeat: int = 300,
        logger: logging.Logger | None = None,
    ):
        self._model = model
        self._url = url
        self._heartbeat = heartbeat
        self._logger = logger or logging.getLogger(__name__)
        self._conn = None
        self._channel = None
        self._connect()

    def _connect(self):
        params = pika.URLParameters(self._url)
        params.heartbeat = self._heartbeat
        params.blocked_connection_timeout = 300
        self._conn = pika.BlockingConnection(params)
        self._channel = self._conn.channel()

    def _reconnect(self):
        for attempt in range(MAX_RETRIES):
            try:
                self._logger.info(
                    f"Reconectando a RabbitMQ (intento {attempt + 1}/{MAX_RETRIES})..."
                )
                self._connect()
                self._logger.info("Reconexión exitosa")
                return
            except Exception as e:
                self._logger.error(f"Error reconectando: {e}")
                time.sleep(RETRY_DELAY * (attempt + 1))
        raise RuntimeError("No se pudo reconectar a RabbitMQ")

    def _declare(self, queue: str):
        self._channel.queue_declare(queue=queue, durable=True)

    def declare(self, queue: str):
        self._declare(queue)

    def set_callback(
        self, queue: str, callback: Callable[[Message[T]], None], prefetch: int = 1
    ) -> None:
        """Registra el callback sin iniciar el loop de consumo."""
        self._declare(queue)
        self._channel.basic_qos(prefetch_count=prefetch)

        def _on_message(ch, method, properties, body):
            try:
                data = json.loads(body)
                typed = self._model(**data)
                callback(Message(seq=method.delivery_tag, body=typed))
            except Exception as e:
                self._logger.error(f"Error procesando mensaje: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self._channel.basic_consume(queue=queue, on_message_callback=_on_message)
        self._logger.info(f"Escuchando queue: {queue}")

    def process_events(self, time_limit: float = 1.0) -> None:
        """Procesa eventos pendientes sin bloquear indefinidamente."""
        try:
            self._conn.process_data_events(time_limit=time_limit)
        except pika.exceptions.ConnectionClosedByBroker as e:
            self._logger.warning(f"Conexión cerrada por RabbitMQ: {e}, reconectando...")
            self._reconnect()
        except pika.exceptions.AMQPConnectionError as e:
            self._logger.warning(f"Error de conexión AMQP: {e}, reconectando...")
            self._reconnect()

    def publish(self, queue: str, message: T) -> None:
        self._declare(queue)
        body = json.dumps(
            (
                dataclasses.asdict(message)
                if dataclasses.is_dataclass(message)
                else message
            ),
            ensure_ascii=False,
        )
        self._channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=body,
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )

    def consume(
        self, queue: str, callback: Callable[[Message[T]], None], prefetch: int = 1
    ) -> None:
        """Loop de consumo bloqueante con reconexión automática."""
        while True:
            try:
                self.set_callback(queue, callback, prefetch)
                self._channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker as e:
                self._logger.warning(
                    f"Conexión cerrada por RabbitMQ: {e}, reconectando..."
                )
                self._reconnect()
            except pika.exceptions.AMQPConnectionError as e:
                self._logger.warning(f"Error de conexión AMQP: {e}, reconectando...")
                self._reconnect()
            except pika.exceptions.ChannelClosedByBroker as e:
                self._logger.warning(
                    f"Canal cerrado por RabbitMQ: {e}, reconectando..."
                )
                self._reconnect()
            except KeyboardInterrupt:
                self._logger.info("Interrupción manual, deteniendo consumo...")
                self._channel.stop_consuming()
                break

    def ack(self, seq: int) -> None:
        self._channel.basic_ack(delivery_tag=seq)

    def nack(self, seq: int, requeue: bool = False) -> None:
        self._channel.basic_nack(delivery_tag=seq, requeue=requeue)

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
