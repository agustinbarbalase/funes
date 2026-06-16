from app.llms.llm import LLM
from app.models.ephemeris import Ephemeris, EphemerisResponse
from app.prompts.ephemeris import EPHEMERIS_PROMPT
from app.retrievers.retriever import Retriever
from app.services.ephemeris_service import EphemerisService


class RAGEphemerisService(EphemerisService):

    def __init__(self, retriever: Retriever, llm: LLM):
        self._retriever = retriever
        self._llm = llm

    async def get_ephemeris(self, day: int, month: int) -> list[Ephemeris]:
        query = f"¿Qué efemérides ocurrieron el {day}/{month}?"
        return await self._search(query, day=day, month=month, randomize=True)

    async def get_ephemeris_by_query(self, query: str) -> list[Ephemeris]:
        return await self._search(query)

    async def _search(
        self, query: str, day: int | None = None, month: int | None = None, randomize: bool = False
    ) -> list[Ephemeris]:
        documents = await self._retriever.retrieve(query=query, limit=20, day=day, month=month, randomize=randomize)
        print(f"documents retrieved: {len(documents)}")
        for d in documents[:3]:
            print(f"  doc: {d.metadata.get('title')}")

        metadata_by_id: dict[int, dict] = {
            d.metadata.get("id"): d.metadata for d in documents
        }

        context = "\n\n".join(f"""
            ID: {d.metadata.get('id')}
            Fecha: {d.metadata.get('date')}
            Tipo: {d.metadata.get('type')}
            Título: {d.metadata.get('title')}
            Descripción: {d.content}
            """ for d in documents)

        prompt = EPHEMERIS_PROMPT.format(context=context, query=query)

        response = self._llm.invoke_structured(
            prompt=prompt,
            output_type=EphemerisResponse,
        )
        print(f"LLM response: {response}")
        print(f"LLM ephemerides: {response.ephemerides}")

        for ephemeris in response.ephemerides:
            original = metadata_by_id.get(ephemeris.source_id)

            if original:
                ephemeris.images = original.get("images") or []
                ephemeris.urls = original.get("urls") or []

        return response.ephemerides
