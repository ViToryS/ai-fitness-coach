
from __future__ import annotations

import time

from src.exercises.plank.phase.plank_angle_calculator import (
    PlankAngleCalculator,
)


class PlankPhaseAlgorithm:

    READY = "Исходное положение"
    HOLD = "Удержание планки"
    NO_POSE = "Поза не обнаружена"

    BODY_LINE_MIN = 165.0
    BODY_LINE_MAX = 180.0

    ELBOW_MIN = 80.0
    ELBOW_MAX = 100.0

    ALIGNMENT_MAX = 0.15

    READY_TIME = 0.8
    INVALID_TIMEOUT = 0.5
    LOST_TIMEOUT = 0.8

    SMOOTHING_WINDOW = 5

    def __init__(self):
        self._calculator = PlankAngleCalculator()
        self.reset()

    def reset(self):
        self._phase = self.READY

        self._valid_since = None
        self._invalid_since = None
        self._last_valid_time = time.monotonic()

        self._history = []

    @property
    def phase(self):
        return self._phase

    def update(self, landmarks):
        now = time.monotonic()

        if landmarks is None:
            if now - self._last_valid_time > self.LOST_TIMEOUT:
                self._phase = self.NO_POSE
                self._clear_state()

            return self._phase

        metrics = self._calculator.calculate(landmarks)

        if metrics is None:
            if now - self._last_valid_time > self.LOST_TIMEOUT:
                self._phase = self.NO_POSE
                self._clear_state()

            return self._phase

        self._last_valid_time = now

        if self._phase == self.NO_POSE:
            self.reset()

        self._history.append(metrics)

        if len(self._history) > self.SMOOTHING_WINDOW:
            self._history.pop(0)

        smoothed = self._smooth_metrics()

        if smoothed is None:
            return self._phase

        is_valid = self._is_valid_position(smoothed)

        if is_valid:
            self._invalid_since = None

            if self._valid_since is None:
                self._valid_since = now

            if (
                self._phase == self.READY
                and now - self._valid_since >= self.READY_TIME
            ):
                self._phase = self.HOLD

        else:
            self._valid_since = None

            if self._invalid_since is None:
                self._invalid_since = now

            if (
                self._phase == self.HOLD
                and now - self._invalid_since >= self.INVALID_TIMEOUT
            ):
                self._phase = self.READY

        return self._phase

    def _smooth_metrics(self):
        if not self._history:
            return None

        body_angles = [
            item["body_line_angle"]
            for item in self._history
        ]

        elbow_angles = [
            item["elbow_angle_mean"]
            for item in self._history
        ]

        alignment_values = [
            item["elbow_alignment_deviation"]
            for item in self._history
            if item["elbow_alignment_deviation"] is not None
        ]

        return {
            "body_line_angle": float(
                sum(body_angles) / len(body_angles)
            ),
            "elbow_angle_mean": float(
                sum(elbow_angles) / len(elbow_angles)
            ),
            "elbow_alignment_deviation": (
                float(sum(alignment_values) / len(alignment_values))
                if alignment_values
                else None
            ),
        }

    def _is_valid_position(self, metrics):
        body_angle = metrics["body_line_angle"]
        elbow_angle = metrics["elbow_angle_mean"]

        if not (
            self.BODY_LINE_MIN
            <= body_angle
            <= self.BODY_LINE_MAX
        ):
            return False

        if not (
            self.ELBOW_MIN
            <= elbow_angle
            <= self.ELBOW_MAX
        ):
            return False

        alignment = metrics["elbow_alignment_deviation"]

        if (
            alignment is not None
            and alignment > self.ALIGNMENT_MAX
        ):
            return False

        return True

    def _clear_state(self):
        self._valid_since = None
        self._invalid_since = None
        self._history.clear()

    def close(self):
        self.reset()
