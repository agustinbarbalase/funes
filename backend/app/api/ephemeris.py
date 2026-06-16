from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.session import get_connection
from app.embeddings.fast_embed_embedding import FastEmbedEmbedding
from app.llms.ollama_llm import OllamaLLM
from app.repositories.ephemeris_repository import EphemerisRepository
from app.retrievers.pgvector_retriever import PGVectorRetriever
from app.services.rag_ephemeris_service import RAGEphemerisService

router = APIRouter(prefix="/ephemeris", tags=["ephemeris"])

_embedder = FastEmbedEmbedding()


def get_ephemeris_service(
    conn: AsyncConnection = Depends(get_connection),
) -> RAGEphemerisService:
    repository = EphemerisRepository(conn)
    retriever = PGVectorRetriever(repository=repository, embedding_model=_embedder)
    return RAGEphemerisService(retriever=retriever, llm=OllamaLLM())


@router.get("/search")
async def search_ephemeris(
    query: str,
    service: RAGEphemerisService = Depends(get_ephemeris_service),
):
    print(f"search query: {query!r}")
    result = await service.get_ephemeris_by_query(query=query)
    print(f"search result: {result}")
    return result


@router.get("/{month}/{day}")
async def get_ephemeris(
    month: int,
    day: int,
    service: RAGEphemerisService = Depends(get_ephemeris_service),
):
    return await service.get_ephemeris(day=day, month=month)
