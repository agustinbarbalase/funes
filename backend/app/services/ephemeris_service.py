from abc import ABC, abstractmethod
from app.models.ephemeris import Ephemeris


class EphemerisService(ABC):
    @abstractmethod
    async def get_ephemeris(self, day: int, month: int) -> list[Ephemeris]:
        pass

    @abstractmethod
    async def get_ephemeris_by_query(self, query: str) -> list[Ephemeris]:
        pass
