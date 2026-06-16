from abc import ABC
from abc import abstractmethod


class TooManyRequestsError(Exception):
    pass


class Embedder(ABC):

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass

    @abstractmethod
    def embed_many(self, texts: list[str]) -> list[list[float]]:
        pass
