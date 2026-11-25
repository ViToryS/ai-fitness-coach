
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.exercises.base.phase import ExercisePhase
from src.models.viewpoint import ViewpointResult


@dataclass(frozen=True)
class ExerciseAnalysisResult:
    """Результаты анализа одного кадра упражнения."""

    phase: ExercisePhase | None = None
    viewpoint: ViewpointResult | None = None


class ExerciseAnalyzer(ABC):
    """Общий интерфейс анализатора упражнения."""

    @abstractmethod
    def update(self, landmarks, frame_shape) -> ExerciseAnalysisResult:
        """Анализирует один кадр и возвращает результаты."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Сбрасывает внутреннее состояние анализатора."""
        pass
