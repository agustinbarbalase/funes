from app.repositories.ephemeris_repository import EphemerisRepository
from app.retrievers.document import Document
from app.retrievers.retriever import Retriever


class PGVectorRetriever(Retriever):

    def __init__(self, repository: EphemerisRepository, embedding_model):
        self._repository = repository
        self._embedding_model = embedding_model

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        day: int | None = None,
        month: int | None = None,
        randomize: bool = False,
    ) -> list[Document]:

        query_embedding = self._embedding_model.embed(query)
        records = await self._repository.find_similar(
            embedding=query_embedding,
            query=query if not randomize else None,
            limit=limit,
            day=day,
            month=month,
            randomize=randomize,
        )

        documents: list[Document] = []

        for r in records:
            date = f"{r.day}/{r.month}" + (f"/{r.year}" if r.year else "")

            content = f"{r.title}. {r.description}. (Fecha: {date}, Tipo: {r.type})"

            documents.append(
                Document(
                    content=content,
                    metadata={
                        "id": r.id,
                        "date": date,
                        "type": r.type,
                        "title": r.title,
                        "images": r.images,
                        "urls": r.urls,
                    },
                )
            )

        return documents
