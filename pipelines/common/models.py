from dataclasses import dataclass, field


@dataclass
class Task:
    """Tarea emitida por el producer: un día/mes a procesar."""

    day: int
    month: int


@dataclass
class RawPage:
    """Respuesta cruda de Wikipedia onthisday para un día/mes."""

    day: int
    month: int
    data: dict


@dataclass
class Ephemeris:
    """Efeméride procesada, lista para validar y cargar."""

    day: int
    month: int
    year: int | None
    date: str
    type: str
    title: str
    description: str
    images: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)


@dataclass
class ValidEphemeris(Ephemeris):
    """Efeméride validada y sanitizada, lista para cargar."""

    pass
