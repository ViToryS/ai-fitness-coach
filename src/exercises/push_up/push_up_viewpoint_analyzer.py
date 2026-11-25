
from src.exercises.base.analysis_event import (
    AnalysisEvent,
    ViewpointChanged,
)
from src.exercises.base.frame_analyzer import FrameAnalyzer
from src.exercises.base.viewpoint_detector import ViewpointDetector
from src.models.viewpoint import Viewpoint


class PushUpViewpointAnalyzer(FrameAnalyzer):

    def __init__(self, detector: ViewpointDetector):
        self.detector = detector
        self._last_viewpoint = Viewpoint.UNKNOWN
        self._viewpoint_count = 0

    def update(self, landmarks, frame_shape) -> list[AnalysisEvent]:
        if landmarks is None:
            self.detector.reset()
            self._last_viewpoint = Viewpoint.UNKNOWN
            return []

        result = self.detector.update(
            landmarks,
            frame_shape,
        )

        if result.viewpoint == Viewpoint.UNKNOWN:
            return []

        if result.viewpoint == self._last_viewpoint:
            return []

        self._last_viewpoint = result.viewpoint
        self._viewpoint_count += 1

        return [
            ViewpointChanged(
                viewpoint=result.viewpoint,
                count=self._viewpoint_count,
            )
        ]

    def reset(self) -> None:
        self.detector.reset()
        self._last_viewpoint = Viewpoint.UNKNOWN
        self._viewpoint_count = 0
