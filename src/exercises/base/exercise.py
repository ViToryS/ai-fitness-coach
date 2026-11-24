from abc import ABC, abstractmethod

from src.exercises.base.phase_detector import PhaseDetector
from src.models.viewpoint import Viewpoint


class Exercise(ABC):
    """Базовое описание упражнения."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_viewpoints(self) -> list[Viewpoint]:
        pass

    @abstractmethod
    def create_phase_detector(self) -> PhaseDetector:
        pass