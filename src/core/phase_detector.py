
from __future__ import annotations

import time
from collections import deque

import numpy as np


class SquatPhaseDetector:
    READY = "Исходное положение"
    DESCENT = "Опускание"
    BOTTOM = "Нижняя точка"
    ASCENT = "Подъём"
    NO_POSE = "Поза не обнаружена"

    VISIBILITY_THRESHOLD = 0.5

    MOVEMENT_THRESHOLD = 0.8

    SMOOTHING_WINDOW = 5
    DIRECTION_WINDOW = 3
    TURN_WINDOW = 4

    STABILITY_THRESHOLD = 1.2

    BOTTOM_ENTRY_THRESHOLD = 1.5


    BOTTOM_EXIT_RISE = 2.4

    LOST_TIMEOUT = 0.8

    def __init__(self):
        self.reset()

    def reset(self):
        self._phase = self.READY

        self._angles = deque(maxlen=self.SMOOTHING_WINDOW)
        self._history = deque(maxlen=self.TURN_WINDOW + 2)

        self._previous_angle = None
        self._previous_time = None
        self._angular_velocity = 0.0

        self._last_valid_time = time.monotonic()

        self._direction = 0

        self._minimum_angle = None
        self._maximum_angle = None

        self._bottom_angle = None

        self._turn_candidate = None

    @property
    def phase(self):
        return self._phase

    def update(self, landmarks):
        now = time.monotonic()

        if landmarks is None:
            if now - self._last_valid_time > self.LOST_TIMEOUT:
                self._phase = self.NO_POSE
                self._clear_motion_history()

            return self._phase

        angle = self._get_knee_angle(landmarks)

        if angle is None:
            if now - self._last_valid_time > self.LOST_TIMEOUT:
                self._phase = self.NO_POSE
                self._clear_motion_history()

            return self._phase

        self._last_valid_time = now

        if self._phase == self.NO_POSE:
            self.reset()

        self._angles.append(angle)
        smoothed_angle = float(np.median(self._angles))

        if self._previous_angle is None:
            self._previous_angle = smoothed_angle
            self._previous_time = now
            self._history.append(smoothed_angle)

            self._minimum_angle = smoothed_angle
            self._maximum_angle = smoothed_angle

            return self._phase

        dt = now - self._previous_time

        if dt <= 0:
            return self._phase

        angle_delta = smoothed_angle - self._previous_angle
        self._angular_velocity = angle_delta / dt

        self._history.append(smoothed_angle)

        self._update_direction()
        self._update_phase(smoothed_angle)

        self._previous_angle = smoothed_angle
        self._previous_time = now

        return self._phase

    def _update_direction(self):
        if len(self._history) < self.DIRECTION_WINDOW + 1:
            return

        values = list(self._history)

        differences = [
            values[i] - values[i - 1]
            for i in range(1, len(values))
        ]

        recent = differences[-self.DIRECTION_WINDOW:]

        positive = sum(
            delta > self.MOVEMENT_THRESHOLD
            for delta in recent
        )

        negative = sum(
            delta < -self.MOVEMENT_THRESHOLD
            for delta in recent
        )

        required = self.DIRECTION_WINDOW - 1

        if negative >= required:
            self._direction = -1

        elif positive >= required:
            self._direction = 1

    def _update_phase(self, angle):
        if self._phase == self.READY:
            self._update_ready(angle)

        elif self._phase == self.DESCENT:
            self._update_descent(angle)

        elif self._phase == self.BOTTOM:
            self._update_bottom(angle)

        elif self._phase == self.ASCENT:
            self._update_ascent(angle)

    def _update_ready(self, angle):
        if self._direction == -1:
            self._phase = self.DESCENT
            self._minimum_angle = angle
            self._bottom_angle = None
            self._turn_candidate = None

    def _update_descent(self, angle):
        if self._minimum_angle is None:
            self._minimum_angle = angle

        self._minimum_angle = min(
            self._minimum_angle,
            angle,
        )

        if self._is_stable():
            distance_from_minimum = (
                angle - self._minimum_angle
            )

            if distance_from_minimum <= self.BOTTOM_ENTRY_THRESHOLD:
                self._phase = self.BOTTOM
                self._bottom_angle = angle
                self._turn_candidate = None
                return

        if self._direction == -1:
            self._turn_candidate = None
            return

        if self._direction == 1:
            rise = angle - self._minimum_angle

            if rise >= self.MOVEMENT_THRESHOLD * 2:
                self._phase = self.BOTTOM
                self._bottom_angle = angle
                self._turn_candidate = None

    def _update_bottom(self, angle):
        if self._bottom_angle is None:
            self._bottom_angle = angle


        if (
            self._direction == -1
            and angle < self._bottom_angle - self.MOVEMENT_THRESHOLD
        ):
            self._phase = self.DESCENT
            self._minimum_angle = angle
            self._bottom_angle = None
            self._turn_candidate = None
            return

        if self._direction == 1:
            rise = angle - self._bottom_angle

            if rise >= self.BOTTOM_EXIT_RISE:
                self._phase = self.ASCENT
                self._maximum_angle = angle
                self._bottom_angle = None

    def _update_ascent(self, angle):
        if self._maximum_angle is None:
            self._maximum_angle = angle

        self._maximum_angle = max(
            self._maximum_angle,
            angle,
        )

        if self._direction == -1:
            self._phase = self.DESCENT
            self._minimum_angle = angle
            self._maximum_angle = None
            self._bottom_angle = None
            self._turn_candidate = None
            return


        if self._is_stable():
            self._phase = self.READY
            self._minimum_angle = angle
            self._maximum_angle = angle
            self._bottom_angle = None
            self._turn_candidate = None

    def _is_stable(self):
        if len(self._history) < self.TURN_WINDOW:
            return False

        values = list(self._history)[-self.TURN_WINDOW:]

        variation = max(values) - min(values)

        return variation <= self.STABILITY_THRESHOLD

    def _clear_motion_history(self):
        self._angles.clear()
        self._history.clear()

        self._previous_angle = None
        self._previous_time = None
        self._angular_velocity = 0.0

        self._direction = 0

        self._minimum_angle = None
        self._maximum_angle = None
        self._bottom_angle = None
        self._turn_candidate = None

    def _get_knee_angle(self, landmarks):
        points = np.asarray(landmarks)

        if (
            points.ndim != 2
            or points.shape[0] < 29
            or points.shape[1] < 4
        ):
            return None

        angles = []

        for hip, knee, ankle in (
            (23, 25, 27),
            (24, 26, 28),
        ):
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

        denominator = (
            np.linalg.norm(ba)
            * np.linalg.norm(bc)
        )

        if denominator < 1e-6:
            return None

        cosine = np.dot(ba, bc) / denominator
        cosine = np.clip(cosine, -1.0, 1.0)

        return float(np.degrees(np.arccos(cosine)))
