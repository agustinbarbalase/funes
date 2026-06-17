from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ephemeris import router as ephemeris_router
from app.api.ingest import router as ingest_router
from app.session import init_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Funes",
    description="Historical Ephemeris RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ephemeris_router)
app.include_router(ingest_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.head("/health")
async def health_head():
    return {"status": "ok"}
