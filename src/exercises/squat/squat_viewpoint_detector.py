
from collections import Counter, deque

from src.exercises.base.viewpoint_detector import ViewpointDetector
from src.exercises.squat.viewpoint_detectors.base import (
    extract_squat_features,
)
from src.exercises.squat.viewpoint_detectors.front import FrontViewpointDetector
from src.exercises.squat.viewpoint_detectors.side import SideViewpointDetector
from src.exercises.squat.viewpoint_detectors.diagonal import (
    DiagonalViewpointDetector,
)
from src.models.viewpoint import Viewpoint, ViewpointResult


class SquatViewpointDetector(ViewpointDetector):
    """Определяет передний, боковой и диагональный ракурсы приседания."""

    HISTORY_SIZE = 7
    REQUIRED_VOTES = 5
    MIN_SCORE = 0.18
    MIN_SCORE_DIFFERENCE = 0.05

    def __init__(self):
        self._detectors = {
            Viewpoint.FRONT: FrontViewpointDetector(),
            Viewpoint.SIDE: SideViewpointDetector(),
            Viewpoint.DIAGONAL: DiagonalViewpointDetector(),
        }
        self._history = deque(maxlen=self.HISTORY_SIZE)

    def update(self, landmarks, frame_shape) -> ViewpointResult:
        features = extract_squat_features(landmarks, frame_shape)

        if features is None:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        scores = {
            viewpoint: detector.score(features)
            for viewpoint, detector in self._detectors.items()
        }

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        best_viewpoint, best_score = ranked[0]
        second_score = ranked[1][1]

        if best_score < self.MIN_SCORE:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        if best_score - second_score < self.MIN_SCORE_DIFFERENCE:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        self._history.append(best_viewpoint)

        viewpoint, count = Counter(self._history).most_common(1)[0]

        if count < self.REQUIRED_VOTES:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        confidence = count / len(self._history)

        return ViewpointResult(
            viewpoint,
            float(confidence),
        )

    def reset(self):
        self._history.clear()
