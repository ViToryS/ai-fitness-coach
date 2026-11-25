
from __future__ import annotations

from collections import deque

import numpy as np


class MovementAnalyzer:
    """Анализирует динамику изменения угла во времени."""

    def __init__(
        self,
        smoothing_window: int = 5,
        direction_window: int = 3,
        history_window: int = 4,
        movement_threshold: float = 0.8,
        stability_threshold: float = 1.2,
    ):
        self.smoothing_window = smoothing_window
        self.direction_window = direction_window
        self.history_window = history_window
        self.movement_threshold = movement_threshold
        self.stability_threshold = stability_threshold

        self.reset()

    def reset(self):
        """Сбрасывает историю и состояние анализа движения."""
        self._angles = deque(maxlen=self.smoothing_window)
        self._history = deque(maxlen=self.history_window + 2)

        self._previous_angle = None
        self._previous_time = None
        self._angular_velocity = 0.0

        self._direction = 0

    @property
    def direction(self) -> int:
        """Направление движения: -1, 0 или 1."""
        return self._direction

    def update(self, angle: float, timestamp: float) -> tuple[float, bool, bool]:
        """
        Обрабатывает новый угол.

        Возвращает:
            smoothed_angle — сглаженный угол;
            is_first_sample — является ли кадр первым;
            can_update_phase — можно ли обновлять фазу.
        """
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

        angle_delta = smoothed_angle - self._previous_angle
        self._angular_velocity = angle_delta / dt

        self._history.append(smoothed_angle)

        self._update_direction()

        self._previous_angle = smoothed_angle
        self._previous_time = timestamp

        return smoothed_angle, False, True

    def _update_direction(self):
        if len(self._history) < self.direction_window + 1:
            return

        values = list(self._history)

        differences = [
            values[i] - values[i - 1]
            for i in range(1, len(values))
        ]

        recent = differences[-self.direction_window:]

        positive = sum(
            delta > self.movement_threshold
            for delta in recent
        )

        negative = sum(
            delta < -self.movement_threshold
            for delta in recent
        )

        required = self.direction_window - 1

        if negative >= required:
            self._direction = -1

        elif positive >= required:
            self._direction = 1

    def is_stable(self) -> bool:
        """Проверяет стабильность угла на последних кадрах."""
        if len(self._history) < self.history_window:
            return False

        values = list(self._history)[-self.history_window:]

        variation = max(values) - min(values)

        return variation <= self.stability_threshold
