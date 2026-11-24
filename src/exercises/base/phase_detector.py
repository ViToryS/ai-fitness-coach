from abc import ABC, abstractmethod

from src.exercises.base.phase import ExercisePhase


class PhaseDetector(ABC):
    """Базовый интерфейс для определения фаз упражнения."""

    @abstractmethod
    def update(self, landmarks) -> ExercisePhase | None:
        pass

    @abstractmethod
    def reset(self):
        pass