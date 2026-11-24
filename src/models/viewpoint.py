
from dataclasses import dataclass
from enum import Enum


class Viewpoint(Enum):
    """Хранит общие типы ракурсов камеры."""

    FRONT = "Передний ракурс"
    SIDE = "Боковой ракурс"
    DIAGONAL = "Диагональный ракурс"
    UNKNOWN = "Неизвестный ракурс"


@dataclass(frozen=True)
class ViewpointResult:
    """Хранит определённый ракурс и уверенность системы."""

    viewpoint: Viewpoint
    confidence: float
