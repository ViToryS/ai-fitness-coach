from abc import ABC, abstractmethod

from src.models.viewpoint import ViewpointResult


class ViewpointDetector(ABC):
    """Базовый интерфейс определения ракурса упражнения."""

    @abstractmethod
    def update(self, landmarks, frame_shape) -> ViewpointResult:
        pass

    @abstractmethod
    def reset(self):
        pass
