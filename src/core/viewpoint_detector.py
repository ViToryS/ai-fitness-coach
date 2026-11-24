
from collections import Counter, deque

import numpy as np

from src.models.viewpoint import Viewpoint, ViewpointResult


class ViewpointDetector:
    """Определяет ракурс пользователя по точкам скелета."""

    VISIBILITY_THRESHOLD = 0.5
    SIDE_THRESHOLD = 0.25
    FRONT_THRESHOLD = 0.45
    HISTORY_SIZE = 7
    REQUIRED_VOTES = 5

    def __init__(self):
        self._history = deque(maxlen=self.HISTORY_SIZE)

    def update(self, landmarks, frame_shape) -> ViewpointResult:
        result = self._detect(landmarks, frame_shape)

        if result.viewpoint == Viewpoint.UNKNOWN:
            return result

        self._history.append(result.viewpoint)

        viewpoint, count = Counter(self._history).most_common(1)[0]

        if count < self.REQUIRED_VOTES:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        confidence = count / len(self._history)

        return ViewpointResult(viewpoint, confidence)

    def reset(self):
        self._history.clear()

    def _detect(self, landmarks, frame_shape) -> ViewpointResult:
        points = np.asarray(landmarks)

        if points.ndim != 2 or points.shape[0] < 25 or points.shape[1] < 4:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        if frame_shape is None or len(frame_shape) < 2:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        height, width = frame_shape[:2]

        indices = [11, 12, 23, 24]
        joints = points[indices]

        if not np.all(np.isfinite(joints)):
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        if np.min(joints[:, 3]) < self.VISIBILITY_THRESHOLD:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        left_shoulder, right_shoulder, left_hip, right_hip = joints[:, :2]

        shoulder_width = abs(left_shoulder[0] - right_shoulder[0]) * width
        hip_width = abs(left_hip[0] - right_hip[0]) * width

        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2

        torso_height = abs(shoulder_center[1] - hip_center[1]) * height

        if torso_height < 1e-6:
            return ViewpointResult(Viewpoint.UNKNOWN, 0.0)

        body_width = (shoulder_width + hip_width) / 2
        ratio = body_width / torso_height

        if ratio <= self.SIDE_THRESHOLD:
            confidence = 1 - ratio / self.SIDE_THRESHOLD
            return ViewpointResult(
                Viewpoint.SIDE,
                float(np.clip(confidence, 0, 1))
            )

        if ratio >= self.FRONT_THRESHOLD:
            confidence = (ratio - self.FRONT_THRESHOLD) / self.FRONT_THRESHOLD
            return ViewpointResult(
                Viewpoint.FRONT,
                float(np.clip(confidence, 0, 1))
            )

        return ViewpointResult(Viewpoint.UNKNOWN, 0.0)
