from src.exercises.base.analysis_event import (
    AnalysisEvent,
    PhaseChanged,
)
from src.exercises.base.frame_analyzer import FrameAnalyzer
from src.exercises.plank.plank_phase_detector import (
    PlankPhaseDetector,
)


class PlankPhaseAnalyzer(FrameAnalyzer):

    def __init__(self, detector: PlankPhaseDetector):
        self.detector = detector
        self._last_phase_code = None

    def update(
        self,
        landmarks,
        frame_shape,
    ) -> list[AnalysisEvent]:

        phase = self.detector.update(
            landmarks,
            frame_shape,
        )

        if phase is None:
            self._last_phase_code = None
            return []

        if phase.code == self._last_phase_code:
            return []

        self._last_phase_code = phase.code

        return [
            PhaseChanged(phase=phase)
        ]

    def reset(self):
        self.detector.reset()
        self._last_phase_code = None