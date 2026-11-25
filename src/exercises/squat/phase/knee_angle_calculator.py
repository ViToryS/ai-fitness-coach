
from __future__ import annotations

import numpy as np


class KneeAngleCalculator:
    """Вычисляет средний угол левого и правого колена по landmarks."""

    def __init__(self, visibility_threshold: float = 0.5):
        self.visibility_threshold = visibility_threshold

    def calculate(self, landmarks) -> float | None:
        """
        Вычисляет средний угол коленей.

        Используются точки MediaPipe:
        левая нога: 23, 25, 27;
        правая нога: 24, 26, 28.

        Возвращает None, если координаты некорректны
        или обе ноги недостаточно видимы.
        """
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

            if np.min(joints[:, 3]) < self.visibility_threshold:
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
    def _calculate_angle(a, b, c) -> float | None:
        """Вычисляет угол ABC в градусах."""
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
