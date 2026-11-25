
from src.exercises.base.exercise_analyzer import (
    ExerciseAnalyzer,
    ExerciseAnalysisResult,
)
from src.exercises.base.phase_detector import PhaseDetector
from src.exercises.base.viewpoint_detector import ViewpointDetector
from src.models.viewpoint import Viewpoint, ViewpointResult


class SquatAnalyzer(ExerciseAnalyzer):
    """Объединяет анализ фаз и ракурса для приседаний."""

    def __init__(
        self,
        phase_detector: PhaseDetector,
        viewpoint_detector: ViewpointDetector,
    ):
        self.phase_detector = phase_detector
        self.viewpoint_detector = viewpoint_detector

    def update(self, landmarks, frame_shape) -> ExerciseAnalysisResult:

        phase = self.phase_detector.update(landmarks)

        if landmarks is None:
            self.viewpoint_detector.reset()
            viewpoint_result = ViewpointResult(
                Viewpoint.UNKNOWN,
                0.0,
            )
        else:
            viewpoint_result = self.viewpoint_detector.update(
                landmarks,
                frame_shape,
            )

        return ExerciseAnalysisResult(
            phase=phase,
            viewpoint=viewpoint_result,
        )

    def reset(self) -> None:
        self.phase_detector.reset()
        self.viewpoint_detector.reset()
