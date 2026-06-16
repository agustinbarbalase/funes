import asyncio
import time
from dataclasses import dataclass

from app.embeddings.embedding import Embedder
from app.models.ephemeris import Ephemeris
from app.repositories.ephemeris_repository import EphemerisRepository, EphemerisRecord


@dataclass
class IngestResult:
    day: int
    month: int
    inserted: int
    embedded: int
    skipped: int


class IngestService:

    def __init__(self, repository: EphemerisRepository, embedder: Embedder):
        self._repository = repository
        self._embedder = embedder

    async def ingest(
        self, day: int, month: int, ephemerides: list[Ephemeris]
    ) -> IngestResult:
        # 1. Dedup por título
        t0 = time.time()
        existing = await self._repository.existing_titles(day, month)
        new = [e for e in ephemerides if e.title not in existing]

        if not new:
            return IngestResult(
                day=day,
                month=month,
                inserted=0,
                embedded=0,
                skipped=len(ephemerides),
            )

        records = [_to_record(day, month, e) for e in new]
        ids = await self._repository.insert_many(records)

        texts = [_to_embedding_text(e) for e in new]
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(None, self._embedder.embed_many, texts)

        await self._repository.update_embeddings(list(zip(ids, embeddings)))

        return IngestResult(
            day=day,
            month=month,
            inserted=len(new),
            embedded=len(new),
            skipped=len(ephemerides) - len(new),
        )


def _to_record(day: int, month: int, e: Ephemeris) -> EphemerisRecord:
    year = None
    parts = e.date.split("/")
    if len(parts) == 3 and parts[2].isdigit():
        year = int(parts[2])

    return EphemerisRecord(
        id=None,
        day=day,
        month=month,
        year=year,
        type=e.type.value,
        title=e.title,
        description=e.description,
        images=e.images,
        urls=e.urls,
    )


def _to_embedding_text(e: Ephemeris) -> str:
    sentences = e.description.split(".")[:2]
    short_desc = ". ".join(s.strip() for s in sentences if s.strip())
    return f"{e.type} | {e.date} | {e.title} | {short_desc}"
