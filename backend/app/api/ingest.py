from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel

from app.session import get_connection
from app.embeddings.fast_embed_embedding import FastEmbedEmbedding
from app.embeddings.embedding import TooManyRequestsError
from app.models.ephemeris import Ephemeris
from app.repositories.ephemeris_repository import EphemerisRepository
from app.services.ingest_service import IngestService

router = APIRouter(prefix="/ingest", tags=["ingest"])

_embedder = FastEmbedEmbedding()


class IngestRequest(BaseModel):
    ephemerides: list[Ephemeris]


class IngestResponse(BaseModel):
    day: int
    month: int
    inserted: int
    embedded: int
    skipped: int


def get_ingest_service(
    conn: AsyncConnection = Depends(get_connection),
) -> IngestService:
    repository = EphemerisRepository(conn)
    return IngestService(repository=repository, embedder=_embedder)


@router.post("/{day}/{month}", response_model=IngestResponse)
async def ingest(
    day: int,
    month: int,
    body: IngestRequest,
    service: IngestService = Depends(get_ingest_service),
):
    if not (1 <= day <= 31 and 1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Fecha inválida")

    try:
        result = await service.ingest(
            day=day, month=month, ephemerides=body.ephemerides
        )
    except TooManyRequestsError:
        raise HTTPException(status_code=429, detail="Cohere rate limit excedido")

    return IngestResponse(
        day=result.day,
        month=result.month,
        inserted=result.inserted,
        embedded=result.embedded,
        skipped=result.skipped,
    )
