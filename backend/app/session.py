import os
from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async

DATABASE_URL = os.environ["DATABASE_URL"]

_pool: AsyncConnectionPool | None = None


async def init_pool() -> None:
    global _pool
    _pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        open=False,
        min_size=4,
        max_size=20,
        configure=_configure_conn,
    )
    await _pool.open()


async def _configure_conn(conn) -> None:
    await register_vector_async(conn)


async def close_pool() -> None:
    if _pool:
        await _pool.close()


async def get_connection():
    async with _pool.connection() as conn:
        yield conn
