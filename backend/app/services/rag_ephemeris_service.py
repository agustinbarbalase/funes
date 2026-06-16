import os
import json
import redis

from app.llms.llm import LLM
from app.models.ephemeris import Ephemeris, EphemerisResponse
from app.prompts.ephemeris import EPHEMERIS_PROMPT
from app.retrievers.retriever import Retriever
from app.services.ephemeris_service import EphemerisService

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class RAGEphemerisService(EphemerisService):

    def __init__(self, retriever: Retriever, llm: LLM):
        self._retriever = retriever
        self._llm = llm
        self._cache = redis.from_url(REDIS_URL, decode_responses=True)

    async def get_ephemeris(self, day: int, month: int) -> list[Ephemeris]:
        cache_key = f"ephemeris:date:{month:02d}:{day:02d}"

        cached = self._cache.get(cache_key)
        if cached:
            print(f"Cache HIT: {cache_key}")
            return [Ephemeris(**item) for item in json.loads(cached)]

        query = f"¿Qué efemérides ocurrieron el {day}/{month}?"
        result = await self._search(query, day=day, month=month, randomize=True)

        self._cache.setex(
            cache_key, 86400, json.dumps([e.model_dump() for e in result])
        )
        return result

    async def get_ephemeris_by_query(self, query: str) -> list[Ephemeris]:
        cache_key = f"ephemeris:search:{hash(query)}"

        cached = self._cache.get(cache_key)
        if cached:
            print(f"Cache HIT: {cache_key}")
            return [Ephemeris(**item) for item in json.loads(cached)]

        result = await self._search(query)

        self._cache.setex(cache_key, 3600, json.dumps([e.model_dump() for e in result]))
        return result

    async def _search(
        self,
        query: str,
        day: int | None = None,
        month: int | None = None,
        randomize: bool = False,
    ) -> list[Ephemeris]:
        documents = await self._retriever.retrieve(
            query=query, limit=20, day=day, month=month, randomize=randomize
        )

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

        for ephemeris in response.ephemerides:
            original = metadata_by_id.get(ephemeris.source_id)

            if original:
                ephemeris.images = original.get("images") or []
                ephemeris.urls = original.get("urls") or []

        return response.ephemerides
