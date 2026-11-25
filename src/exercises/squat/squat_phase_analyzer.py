from src.exercises.base.analysis_event import (
    AnalysisEvent,
    PhaseChanged,
)
from src.exercises.base.frame_analyzer import FrameAnalyzer
from src.exercises.base.phase_detector import PhaseDetector


class SquatPhaseAnalyzer(FrameAnalyzer):

    def __init__(self, detector: PhaseDetector):
        self.detector = detector
        self._last_phase_code = None

    def update(self, landmarks, frame_shape) -> list[AnalysisEvent]:
        phase = self.detector.update(landmarks)

        if phase is None:
            self._last_phase_code = None
            return []

        if phase.code == self._last_phase_code:
            return []

        self._last_phase_code = phase.code

        return [
            PhaseChanged(phase=phase)
        ]

    def reset(self) -> None:
        self.detector.reset()
        self._last_phase_code = None