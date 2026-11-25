
from collections import Counter, deque

import numpy as np

from src.exercises.base.viewpoint_detector import ViewpointDetector
from src.models.viewpoint import Viewpoint, ViewpointResult


class PlankViewpointDetector(ViewpointDetector):

    VISIBILITY_THRESHOLD = 0.5

    HISTORY_SIZE = 7
    REQUIRED_VOTES = 5

    SIDE_THRESHOLD = 0.20
    FRONT_THRESHOLD = 0.45

    def __init__(self):
        self._history = deque(maxlen=self.HISTORY_SIZE)

    def update(self, landmarks, frame_shape) -> ViewpointResult:
        result = self._detect(landmarks)

        if result.viewpoint == Viewpoint.UNKNOWN:
            return result

        self._history.append(result.viewpoint)

        viewpoint, count = Counter(
            self._history
        ).most_common(1)[0]

        if count < self.REQUIRED_VOTES:
            return ViewpointResult(
                Viewpoint.UNKNOWN,
                0.0,
            )

        return ViewpointResult(
            viewpoint,
            float(count / len(self._history)),
        )

    def reset(self):
        self._history.clear()

    def _detect(self, landmarks):
        points = np.asarray(landmarks)

        if (
            points.ndim != 2
            or points.shape[0] < 29
            or points.shape[1] < 4
        ):
            return ViewpointResult(
                Viewpoint.UNKNOWN,
                0.0,
            )

        indices = [11, 12, 23, 24, 27, 28]
        joints = points[indices]

        if not np.all(np.isfinite(joints)):
            return ViewpointResult(
                Viewpoint.UNKNOWN,
                0.0,
            )

        if np.min(joints[:, 3]) < self.VISIBILITY_THRESHOLD:
            return ViewpointResult(
                Viewpoint.UNKNOWN,
                0.0,
            )

        shoulder_width = np.linalg.norm(
            points[11, :2] - points[12, :2]
        )

        hip_width = np.linalg.norm(
            points[23, :2] - points[24, :2]
        )

        shoulder_center = (
            points[11, :2] + points[12, :2]
        ) / 2

        ankle_center = (
            points[27, :2] + points[28, :2]
        ) / 2

        body_length = np.linalg.norm(
            ankle_center - shoulder_center
        )

        if body_length < 1e-6:
            return ViewpointResult(
                Viewpoint.UNKNOWN,
                0.0,
            )

        width_ratio = (
            shoulder_width + hip_width
        ) / (2 * body_length)

        if width_ratio < self.SIDE_THRESHOLD:
            return ViewpointResult(
                Viewpoint.SIDE,
                float(
                    np.clip(
                        1.0 - width_ratio / self.SIDE_THRESHOLD,
                        0.0,
                        1.0,
                    )
                ),
            )

        if width_ratio > self.FRONT_THRESHOLD:
            return ViewpointResult(
                Viewpoint.FRONT,
                float(
                    np.clip(
                        (width_ratio - self.FRONT_THRESHOLD)
                        / self.FRONT_THRESHOLD,
                        0.0,
                        1.0,
                    )
                ),
            )

        return ViewpointResult(
            Viewpoint.DIAGONAL,
            0.5,
        )
