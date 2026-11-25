
from __future__ import annotations

import numpy as np


class PlankAngleCalculator:
    """Вычисляет геометрические параметры планки."""

    VISIBILITY_THRESHOLD = 0.5

    def __init__(self, visibility_threshold: float = 0.5):
        self.visibility_threshold = visibility_threshold

    def calculate(self, landmarks) -> dict | None:
        points = np.asarray(landmarks, dtype=np.float32)

        if (
            points.ndim != 2
            or points.shape[0] < 29
            or points.shape[1] < 4
        ):
            return None

        # Точки плеч, таза и голеностопов.
        body_indices = [11, 12, 23, 24, 27, 28]
        body_points = points[body_indices]

        if not np.all(np.isfinite(body_points)):
            return None

        if np.min(body_points[:, 3]) < self.visibility_threshold:
            return None

        left_shoulder = points[11, :2]
        right_shoulder = points[12, :2]

        left_hip = points[23, :2]
        right_hip = points[24, :2]

        left_ankle = points[27, :2]
        right_ankle = points[28, :2]

        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2
        ankle_center = (left_ankle + right_ankle) / 2

        body_line_angle = self._angle(
            shoulder_center,
            hip_center,
            ankle_center,
        )

        if body_line_angle is None:
            return None

        elbow_angles = []
        alignment_deviations = []

        # Вектор продольной оси тела.
        body_axis = ankle_center - shoulder_center
        body_length = np.linalg.norm(body_axis)

        if body_length > 1e-6:
            body_axis = body_axis / body_length
        else:
            body_axis = None

        for shoulder, elbow, wrist in (
            (11, 13, 15),
            (12, 14, 16),
        ):
            joints = points[[shoulder, elbow, wrist]]

            if not np.all(np.isfinite(joints)):
                continue

            if np.min(joints[:, 3]) < self.visibility_threshold:
                continue

            elbow_angle = self._angle(
                joints[0, :2],
                joints[1, :2],
                joints[2, :2],
            )

            if elbow_angle is not None:
                elbow_angles.append(elbow_angle)

            # Отклонение локтя вдоль продольной оси тела.
            if body_axis is not None:
                shoulder_point = joints[0, :2]
                elbow_point = joints[1, :2]

                longitudinal_offset = abs(
                    np.dot(
                        elbow_point - shoulder_point,
                        body_axis,
                    )
                )

                normalized_offset = (
                    longitudinal_offset / body_length
                )

                alignment_deviations.append(
                    float(normalized_offset)
                )

        if not elbow_angles:
            return None

        return {
            "body_line_angle": float(body_line_angle),
            "elbow_angles": elbow_angles,
            "elbow_angle_mean": float(np.mean(elbow_angles)),
            "elbow_alignment_deviation": (
                float(np.mean(alignment_deviations))
                if alignment_deviations
                else None
            ),
        }

    @staticmethod
    def _angle(a, b, c) -> float | None:
        """Вычисляет внутренний угол ABC в градусах."""

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

        return float(
            np.degrees(np.arccos(cosine))
        )
