import numpy as np


class ElbowAngleCalculator:

    def __init__(self, visibility_threshold: float = 0.5):
        self.visibility_threshold = visibility_threshold

    def calculate(self, landmarks) -> float | None:
        points = np.asarray(landmarks)

        if (
            points.ndim != 2
            or points.shape[0] < 17
            or points.shape[1] < 4
        ):
            return None

        angles = []

        for shoulder, elbow, wrist in (
            (11, 13, 15),
            (12, 14, 16),
        ):
            joints = points[[shoulder, elbow, wrist]]

            if not np.all(np.isfinite(joints)):
                continue

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