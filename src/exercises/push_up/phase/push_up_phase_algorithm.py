from __future__ import annotations

import time
from collections import deque

import numpy as np

from src.exercises.push_up.phase.elbow_angle_calculator import (
    ElbowAngleCalculator,
)


class PushUpPhaseAlgorithm:

    READY = "Исходное положение"
    DESCENT = "Опускание"
    BOTTOM = "Нижняя точка"
    ASCENT = "Подъём"
    NO_POSE = "Поза не обнаружена"

    VISIBILITY_THRESHOLD = 0.5

    TOP_ANGLE = 155.0

    MOVEMENT_THRESHOLD = 0.8
    SMOOTHING_WINDOW = 5
    DIRECTION_WINDOW = 3
    TURN_WINDOW = 4

    STABILITY_THRESHOLD = 1.2

    BOTTOM_ENTRY_THRESHOLD = 1.5
    BOTTOM_EXIT_RISE = 2.4

    LOST_TIMEOUT = 0.8

    def __init__(self):
        self._angle_calculator = ElbowAngleCalculator(
            visibility_threshold=self.VISIBILITY_THRESHOLD
        )

        self.reset()

    def reset(self):
        self._phase = self.READY

        self._angles = deque(maxlen=self.SMOOTHING_WINDOW)
        self._history = deque(maxlen=self.TURN_WINDOW + 2)

        self._previous_angle = None
        self._previous_time = None

        self._direction = 0

        self._last_valid_time = time.monotonic()

        self._minimum_angle = None
        self._bottom_angle = None

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

        angle = self._angle_calculator.calculate(landmarks)

        if angle is None:
            if now - self._last_valid_time > self.LOST_TIMEOUT:
                self._phase = self.NO_POSE
                self._clear_motion_history()

            return self._phase

        self._last_valid_time = now

        if self._phase == self.NO_POSE:
            self.reset()

        (
            smoothed_angle,
            is_first_sample,
            can_update_phase,
        ) = self._update_movement(angle, now)

        if is_first_sample:
            self._minimum_angle = smoothed_angle
            return self._phase

        if not can_update_phase:
            return self._phase

        self._update_phase(smoothed_angle)

        return self._phase

    def _update_movement(self, angle, timestamp):
        self._angles.append(angle)

        smoothed_angle = float(np.median(self._angles))

        if self._previous_angle is None:
            self._previous_angle = smoothed_angle
            self._previous_time = timestamp
            self._history.append(smoothed_angle)

            return smoothed_angle, True, False

        dt = timestamp - self._previous_time

        if dt <= 0:
            return smoothed_angle, False, False

        self._history.append(smoothed_angle)

        self._update_direction()

        self._previous_angle = smoothed_angle
        self._previous_time = timestamp

        return smoothed_angle, False, True

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

    def _is_stable(self):
        if len(self._history) < self.TURN_WINDOW:
            return False

        values = list(self._history)[-self.TURN_WINDOW:]

        variation = max(values) - min(values)

        return variation <= self.STABILITY_THRESHOLD

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
                return

        if self._direction == 1:
            rise = angle - self._minimum_angle

            if rise >= self.MOVEMENT_THRESHOLD * 2:
                self._phase = self.BOTTOM
                self._bottom_angle = angle

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
            return

        if self._direction == 1:
            rise = angle - self._bottom_angle

            if rise >= self.BOTTOM_EXIT_RISE:
                self._phase = self.ASCENT
                self._bottom_angle = None

    def _update_ascent(self, angle):
        if self._direction == -1:
            self._phase = self.DESCENT
            self._minimum_angle = angle
            self._bottom_angle = None
            return

        if (
            angle >= self.TOP_ANGLE
            and self._is_stable()
        ):
            self._phase = self.READY
            self._minimum_angle = angle
            self._bottom_angle = None

    def _clear_motion_history(self):
        self._angles.clear()
        self._history.clear()

        self._previous_angle = None
        self._previous_time = None

        self._direction = 0

        self._minimum_angle = None
        self._bottom_angle = None