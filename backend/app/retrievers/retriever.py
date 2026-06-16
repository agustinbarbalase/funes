from abc import ABC, abstractmethod
from app.retrievers.document import Document


class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10) -> list[Document]:
        pass
