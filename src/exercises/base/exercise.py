
from abc import ABC, abstractmethod

from src.exercises.base.exercise_analyzer import ExerciseAnalyzer
from src.models.viewpoint import Viewpoint


class Exercise(ABC):
    """Базовый контракт любого упражнения."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Уникальный программный идентификатор упражнения."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Отображаемое название упражнения."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Краткое описание упражнения."""
        pass

    @property
    @abstractmethod
    def supported_viewpoints(self) -> list[Viewpoint]:
        """Список поддерживаемых ракурсов."""
        pass

    @abstractmethod
    def create_analyzer(self) -> ExerciseAnalyzer:
        """Создаёт анализатор конкретного упражнения."""
        pass
