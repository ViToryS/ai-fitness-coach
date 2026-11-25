from __future__ import annotations

import numpy as np


class PlankAngleCalculator:
    """Вычисляет геометрические параметры положения планки."""

    VISIBILITY_THRESHOLD = 0.5

    def __init__(self, visibility_threshold: float = VISIBILITY_THRESHOLD):
        self.visibility_threshold = visibility_threshold

    def calculate(self, landmarks, frame_shape=None) -> dict | None:
        points = np.asarray(landmarks, dtype=np.float32)

        if (
            points.ndim != 2
            or points.shape[0] < 29
            or points.shape[1] < 4
        ):
            return None

        if frame_shape is None:
            height = 1.0
            width = 1.0
        else:
            if len(frame_shape) < 2:
                return None

            height, width = frame_shape[:2]

            if height <= 0 or width <= 0:
                return None

        valid_mask = (
            np.isfinite(points[:, :4]).all(axis=1)
            & (points[:, 3] >= self.visibility_threshold)
        )

        coordinates = points[:, :3].copy()


        coordinates[:, 0] *= width
        coordinates[:, 1] *= height
        coordinates[:, 2] *= width

        shoulder_center = self._get_center(
            coordinates,
            valid_mask,
            [11, 12],
        )

        hip_center = self._get_center(
            coordinates,
            valid_mask,
            [23, 24],
        )

        ankle_center = self._get_center(
            coordinates,
            valid_mask,
            [27, 28],
        )

        if (
            shoulder_center is None
            or hip_center is None
            or ankle_center is None
        ):
            return None

        torso_angle, torso_length = self._segment_metrics(
            shoulder_center,
            hip_center,
        )

        leg_angle, leg_length = self._segment_metrics(
            hip_center,
            ankle_center,
        )

        if torso_angle is None or leg_angle is None:
            return None

        if torso_length < 1e-6:
            return None

        leg_to_torso_ratio = leg_length / torso_length

        return {
            "torso_angle": torso_angle,
            "leg_angle": leg_angle,
            "leg_to_torso_ratio": float(leg_to_torso_ratio),
        }

    @staticmethod
    def _get_center(
        coordinates: np.ndarray,
        valid_mask: np.ndarray,
        indices: list[int],
    ) -> np.ndarray | None:
        visible_indices = [
            index
            for index in indices
            if valid_mask[index]
        ]

        if not visible_indices:
            return None

        return np.mean(
            coordinates[visible_indices],
            axis=0,
        )

    @staticmethod
    def _segment_metrics(
        start: np.ndarray,
        end: np.ndarray,
    ) -> tuple[float | None, float]:
        """
        Вычисляет наклон сегмента относительно горизонтальной плоскости.

        0 градусов — горизонтальное положение.
        90 градусов — вертикальное положение.
        """

        vector = end - start

        length = float(np.linalg.norm(vector))

        if length < 1e-6:
            return None, 0.0

        horizontal_length = float(
            np.linalg.norm(vector[[0, 2]])
        )

        angle = float(
            np.degrees(
                np.arctan2(
                    abs(vector[1]),
                    horizontal_length,
                )
            )
        )

        return angle, length