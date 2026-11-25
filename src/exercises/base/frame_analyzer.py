from abc import ABC, abstractmethod

from src.exercises.base.analysis_event import AnalysisEvent


class FrameAnalyzer(ABC):

    @abstractmethod
    def update(self, landmarks, frame_shape) -> list[AnalysisEvent]:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass