from src.exercises.base.analysis_event import AnalysisEvent
from src.exercises.base.frame_analyzer import FrameAnalyzer


class ExerciseAnalyzer:

    def __init__(self, analyzers: list[FrameAnalyzer]):
        if not analyzers:
            raise ValueError("Для упражнения необходим хотя бы один анализатор.")

        self._analyzers = tuple(analyzers)

    def update(self, landmarks, frame_shape) -> list[AnalysisEvent]:
        events = []

        for analyzer in self._analyzers:
            events.extend(
                analyzer.update(landmarks, frame_shape)
            )

        return events

    def reset(self) -> None:
        for analyzer in self._analyzers:
            analyzer.reset()