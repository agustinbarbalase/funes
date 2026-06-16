from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar
import logging

T = TypeVar("T")


class Message(Generic[T]):
    def __init__(self, seq: int, body: T):
        self.seq = seq
        self.body = body


class MessageBroker(ABC, Generic[T]):

    @abstractmethod
    def publish(self, queue: str, message: T) -> None:
        pass

    @abstractmethod
    def consume(
        self, queue: str, callback: Callable[[Message[T]], None], prefetch: int = 1
    ) -> None:
        pass

    @abstractmethod
    def ack(self, seq: int) -> None:
        pass

    @abstractmethod
    def nack(self, seq: int, requeue: bool = False) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
