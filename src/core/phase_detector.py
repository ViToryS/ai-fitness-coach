
from __future__ import annotations

import time

from src.exercises.squat.phase.knee_angle_calculator import KneeAngleCalculator
from src.exercises.squat.phase.movement_analyzer import MovementAnalyzer


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
        self._angle_calculator = KneeAngleCalculator(
            visibility_threshold=self.VISIBILITY_THRESHOLD
        )

        self._movement_analyzer = MovementAnalyzer(
            smoothing_window=self.SMOOTHING_WINDOW,
            direction_window=self.DIRECTION_WINDOW,
            history_window=self.TURN_WINDOW,
            movement_threshold=self.MOVEMENT_THRESHOLD,
            stability_threshold=self.STABILITY_THRESHOLD,
        )

        self.reset()

    def reset(self):
        self._phase = self.READY

        self._movement_analyzer.reset()

        self._last_valid_time = time.monotonic()

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
        ) = self._movement_analyzer.update(angle, now)

        if is_first_sample:
            self._minimum_angle = smoothed_angle
            self._maximum_angle = smoothed_angle
            return self._phase

        if not can_update_phase:
            return self._phase

        self._update_phase(smoothed_angle)

        return self._phase

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
        if self._movement_analyzer.direction == -1:
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

        if self._movement_analyzer.is_stable():
            distance_from_minimum = (
                angle - self._minimum_angle
            )

            if distance_from_minimum <= self.BOTTOM_ENTRY_THRESHOLD:
                self._phase = self.BOTTOM
                self._bottom_angle = angle
                self._turn_candidate = None
                return

        if self._movement_analyzer.direction == -1:
            self._turn_candidate = None
            return

        if self._movement_analyzer.direction == 1:
            rise = angle - self._minimum_angle

            if rise >= self.MOVEMENT_THRESHOLD * 2:
                self._phase = self.BOTTOM
                self._bottom_angle = angle
                self._turn_candidate = None

    def _update_bottom(self, angle):
        if self._bottom_angle is None:
            self._bottom_angle = angle

        if (
            self._movement_analyzer.direction == -1
            and angle < self._bottom_angle - self.MOVEMENT_THRESHOLD
        ):
            self._phase = self.DESCENT
            self._minimum_angle = angle
            self._bottom_angle = None
            self._turn_candidate = None
            return

        if self._movement_analyzer.direction == 1:
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

        if self._movement_analyzer.direction == -1:
            self._phase = self.DESCENT
            self._minimum_angle = angle
            self._maximum_angle = None
            self._bottom_angle = None
            self._turn_candidate = None
            return

        if self._movement_analyzer.is_stable():
            self._phase = self.READY
            self._minimum_angle = angle
            self._maximum_angle = angle
            self._bottom_angle = None
            self._turn_candidate = None

    def _clear_motion_history(self):
        self._movement_analyzer.reset()

        self._minimum_angle = None
        self._maximum_angle = None
        self._bottom_angle = None
        self._turn_candidate = None
