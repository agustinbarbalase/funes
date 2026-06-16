from enum import Enum
from pydantic import BaseModel


class EphemerisType(str, Enum):
    BIRTH = "Nacimiento"
    DEATH = "Fallecimiento"
    EVENT = "Evento"


class Ephemeris(BaseModel):
    source_id: int | None = None
    date: str
    type: EphemerisType
    title: str
    description: str
    images: list[str] = []
    urls: list[str] = []


class EphemerisResponse(BaseModel):
    ephemerides: list[Ephemeris]
