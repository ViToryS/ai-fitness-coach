from __future__ import annotations

import time
from collections import deque

import numpy as np

from src.exercises.plank.phase.plank_angle_calculator import (
    PlankAngleCalculator,
)


class PlankPhaseAlgorithm:

    READY = "Исходное положение"
    HOLD = "Удержание планки"
    NO_POSE = "Поза не обнаружена"

    TORSO_ENTER_MAX_ANGLE = 65.0
    LEG_ENTER_MAX_ANGLE = 70.0

    TORSO_EXIT_MAX_ANGLE = 76.0
    LEG_EXIT_MAX_ANGLE = 80.0

    MIN_LEG_TO_TORSO_ENTER_RATIO = 0.80
    MIN_LEG_TO_TORSO_EXIT_RATIO = 0.65

    INITIAL_CONFIRM_TIME = 0.20
    ENTER_HOLD_TIME = 0.25
    EXIT_HOLD_TIME = 0.45

    LOST_TIMEOUT = 0.8

    SMOOTHING_WINDOW = 5

    def __init__(self):
        self._calculator = PlankAngleCalculator()
        self.reset()

    def reset(self):

        self._phase = self.NO_POSE

        self._last_valid_time = None

        self._candidate_phase = None
        self._candidate_since = None

        self._history = deque(
            maxlen=self.SMOOTHING_WINDOW
        )

    @property
    def phase(self):
        return self._phase

    def update(self, landmarks, frame_shape=None):
        now = time.monotonic()

        if landmarks is None:
            return self._handle_missing_pose(now)

        metrics = self._calculator.calculate(
            landmarks,
            frame_shape,
        )

        if metrics is None:
            return self._handle_missing_pose(now)

        self._last_valid_time = now

        self._history.append(metrics)

        smoothed = self._smooth_metrics()

        if smoothed is None:
            return self._phase

        is_plank = self._is_plank_position(smoothed)

        target_phase = (
            self.HOLD
            if is_plank
            else self.READY
        )

        return self._update_phase(
            target_phase,
            now,
        )

    def _is_plank_position(self, metrics: dict) -> bool:
        """
        Определяет, находится ли человек в положении планки.

        При входе используются более строгие пороги.
        Если человек уже находится в HOLD, применяются
        более мягкие пороги для предотвращения мерцания.
        """

        if self._phase == self.HOLD:
            torso_limit = self.TORSO_EXIT_MAX_ANGLE
            leg_limit = self.LEG_EXIT_MAX_ANGLE

            ratio_limit = (
                self.MIN_LEG_TO_TORSO_EXIT_RATIO
            )
        else:
            torso_limit = self.TORSO_ENTER_MAX_ANGLE
            leg_limit = self.LEG_ENTER_MAX_ANGLE

            ratio_limit = (
                self.MIN_LEG_TO_TORSO_ENTER_RATIO
            )

        torso_angle = metrics["torso_angle"]
        leg_angle = metrics["leg_angle"]
        ratio = metrics["leg_to_torso_ratio"]

        if torso_angle > torso_limit:
            return False

        if leg_angle > leg_limit:
            return False

        if ratio < ratio_limit:
            return False

        return True

    def _update_phase(self, target_phase: str, now: float):

        if target_phase == self._phase:
            self._clear_candidate()
            return self._phase

        if target_phase != self._candidate_phase:
            self._candidate_phase = target_phase
            self._candidate_since = now

            return self._phase

        if self._candidate_since is None:
            self._candidate_since = now
            return self._phase

        if self._phase == self.NO_POSE:
            required_time = self.INITIAL_CONFIRM_TIME

        elif target_phase == self.HOLD:
            required_time = self.ENTER_HOLD_TIME

        else:
            required_time = self.EXIT_HOLD_TIME

        elapsed = now - self._candidate_since

        if elapsed < required_time:
            return self._phase

        self._phase = target_phase
        self._clear_candidate()

        return self._phase

    def _smooth_metrics(self) -> dict | None:
        if not self._history:
            return None

        return {
            key: float(
                np.median([
                    item[key]
                    for item in self._history
                ])
            )
            for key in (
                "torso_angle",
                "leg_angle",
                "leg_to_torso_ratio",
            )
        }

    def _handle_missing_pose(self, now: float):
        self._clear_candidate()

        if self._last_valid_time is None:
            return self._phase

        elapsed = now - self._last_valid_time

        if elapsed >= self.LOST_TIMEOUT:
            self._phase = self.NO_POSE
            self._last_valid_time = None
            self._history.clear()

        return self._phase

    def _clear_candidate(self):
        self._candidate_phase = None
        self._candidate_since = None

    def close(self):
        self.reset()