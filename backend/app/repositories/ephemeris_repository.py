"""
EphemerisRepository: única clase que toca la tabla ephemerides.
Tanto el retriever como el ingest service dependen de esta abstracción.
"""

from dataclasses import dataclass, field
from psycopg import AsyncConnection
from pgvector import Vector


@dataclass
class EphemerisRecord:
    id: int | None
    day: int
    month: int
    year: int | None
    type: str
    title: str
    description: str
    images: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    embedding: list[float] | None = None


class EphemerisRepository:

    def __init__(self, connection: AsyncConnection):
        self._conn = connection

    async def find_similar(
        self,
        embedding: list[float],
        query: str | None = None,
        limit: int = 10,
        day: int | None = None,
        month: int | None = None,
        randomize: bool = False,
        vector_weight: float = 0.5,
        text_weight: float = 0.5,
    ) -> list[EphemerisRecord]:
        filters = []
        params = []

        if day is not None:
            filters.append("day = %s")
            params.append(day)
        if month is not None:
            filters.append("month = %s")
            params.append(month)

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        if randomize:
            sql = f"""
                SELECT id, day, month, year, type, title, description, images, urls
                FROM ephemerides
                {where}
                ORDER BY RANDOM()
                LIMIT %s
            """
            params += [limit]

        elif query:
            # Búsqueda híbrida: similitud vectorial + full-text search
            sql = f"""
                SELECT
                    id, day, month, year, type, title, description, images, urls,
                    (
                        {vector_weight} * (1 - (embedding <=> %s)) +
                        {text_weight} * ts_rank(
                            to_tsvector('spanish', coalesce(title, '') || ' ' || coalesce(description, '')),
                            plainto_tsquery('spanish', %s)
                        )
                    ) AS score
                FROM ephemerides
                {where}
                WHERE embedding IS NOT NULL
                ORDER BY score DESC
                LIMIT %s
            """
            params = [Vector(embedding), query] + params + [limit]

        else:
            # Solo similitud vectorial
            sql = f"""
                SELECT id, day, month, year, type, title, description, images, urls
                FROM ephemerides
                {where}
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s
            """
            params += [Vector(embedding), limit]

        async with self._conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

        return [_row_to_record(row) for row in rows]

    async def find_by_day_month(self, day: int, month: int) -> list[EphemerisRecord]:
        sql = """
            SELECT id, day, month, year, type, title, description, images, urls
            FROM ephemerides
            WHERE day = %s AND month = %s
        """
        async with self._conn.cursor() as cur:
            await cur.execute(sql, (day, month))
            rows = await cur.fetchall()

        return [_row_to_record(row) for row in rows]

    async def existing_titles(self, day: int, month: int) -> set[str]:
        sql = "SELECT title FROM ephemerides WHERE day = %s AND month = %s"
        async with self._conn.cursor() as cur:
            await cur.execute(sql, (day, month))
            rows = await cur.fetchall()
        return {row[0] for row in rows}

    async def insert_many(self, records: list[EphemerisRecord]) -> list[int]:
        sql = """
            INSERT INTO ephemerides (day, month, year, type, title, description, images, urls)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        ids = []
        async with self._conn.cursor() as cur:
            for r in records:
                await cur.execute(
                    sql,
                    (
                        r.day,
                        r.month,
                        r.year,
                        r.type,
                        r.title,
                        r.description,
                        r.images,
                        r.urls,
                    ),
                )
                row = await cur.fetchone()
                ids.append(row[0])
        return ids

    async def update_embeddings(self, updates: list[tuple[int, list[float]]]) -> None:
        sql = """
            UPDATE ephemerides
            SET embedding = %s
            WHERE id = %s
        """
        async with self._conn.cursor() as cur:
            for record_id, embedding in updates:
                await cur.execute(sql, (Vector(embedding), record_id))


def _row_to_record(row: tuple) -> EphemerisRecord:
    return EphemerisRecord(
        id=row[0],
        day=row[1],
        month=row[2],
        year=row[3],
        type=row[4],
        title=row[5],
        description=row[6],
        images=row[7] or [],
        urls=row[8] or [],
    )
