
import time
from collections import deque

import numpy as np


class SquatPhaseDetector:
    READY = "Исходное положение"
    DESCENT = "Опускание"
    BOTTOM = "Нижняя точка"
    ASCENT = "Подъём"
    COMPLETE = "Завершение"
    NO_POSE = "Поза не обнаружена"

    VISIBILITY_THRESHOLD = 0.5
    STANDING_ANGLE = 160
    BOTTOM_ANGLE = 110
    RETURN_ANGLE = 165
    SMOOTHING_WINDOW = 5
    LOST_TIMEOUT = 0.8
    COMPLETE_DURATION = 0.45

    def __init__(self):
        self.reset()

    def reset(self):
        self._phase = self.READY
        self._angles = deque(maxlen=self.SMOOTHING_WINDOW)
        self._previous_angle = None
        self._minimum_angle = 180.0
        self._last_valid_time = time.monotonic()
        self._completed_time = None

    @property
    def phase(self):
        return self._phase

    def update(self, landmarks):
        if landmarks is None:
            if time.monotonic() - self._last_valid_time > self.LOST_TIMEOUT:
                self._phase = self.NO_POSE
                self._angles.clear()
                self._previous_angle = None

            return self._phase

        angle = self._get_knee_angle(landmarks)

        if angle is None:
            return self.update(None)

        self._last_valid_time = time.monotonic()

        if self._phase == self.NO_POSE:
            self.reset()

        self._angles.append(angle)
        angle = float(np.median(self._angles))

        previous = self._previous_angle
        change = 0.0 if previous is None else angle - previous

        if self._phase == self.READY:
            if angle < self.STANDING_ANGLE and change < -1.0:
                self._phase = self.DESCENT
                self._minimum_angle = angle

        elif self._phase == self.DESCENT:
            self._minimum_angle = min(self._minimum_angle, angle)

            if angle <= self.BOTTOM_ANGLE:
                self._phase = self.BOTTOM

            elif angle >= self._minimum_angle + 7 and change > 0:
                self._phase = self.BOTTOM

        elif self._phase == self.BOTTOM:
            self._minimum_angle = min(self._minimum_angle, angle)

            if angle >= self._minimum_angle + 7 and change > 0:
                self._phase = self.ASCENT

        elif self._phase == self.ASCENT:
            if previous is not None and change < -4:
                self._phase = self.DESCENT
                self._minimum_angle = angle

            elif angle >= self.RETURN_ANGLE:
                self._phase = self.COMPLETE
                self._completed_time = time.monotonic()

        elif self._phase == self.COMPLETE:
            if angle < self.STANDING_ANGLE - 5:
                self._phase = self.DESCENT
                self._minimum_angle = angle

            elif (
                self._completed_time is not None
                and time.monotonic() - self._completed_time
                >= self.COMPLETE_DURATION
            ):
                self._phase = self.READY
                self._minimum_angle = 180.0

        self._previous_angle = angle
        return self._phase

    def _get_knee_angle(self, landmarks):
        points = np.asarray(landmarks)

        if points.ndim != 2 or points.shape[0] < 29 or points.shape[1] < 4:
            return None

        angles = []

        for hip, knee, ankle in ((23, 25, 27), (24, 26, 28)):
            joints = points[[hip, knee, ankle]]

            if np.min(joints[:, 3]) < self.VISIBILITY_THRESHOLD:
                continue

            angle = self._calculate_angle(
                joints[0, :2],
                joints[1, :2],
                joints[2, :2],
            )

            if angle is not None:
                angles.append(angle)

        if not angles:
            return None

        return float(np.mean(angles))

    @staticmethod
    def _calculate_angle(a, b, c):
        ba = a - b
        bc = c - b

        denominator = np.linalg.norm(ba) * np.linalg.norm(bc)

        if denominator < 1e-6:
            return None

        cosine = np.dot(ba, bc) / denominator
        cosine = np.clip(cosine, -1.0, 1.0)

        return float(np.degrees(np.arccos(cosine)))
