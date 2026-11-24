
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SquatViewpointFeatures:
    """Хранит геометрические признаки корпуса для определения ракурса."""

    width_ratio: float
    depth_ratio: float


class SquatViewpointCandidate(ABC):
    """Базовый интерфейс проверки одного ракурса приседания."""

    @abstractmethod
    def score(self, features: SquatViewpointFeatures) -> float:
        pass


def extract_squat_features(landmarks, frame_shape):
    """Вычисляет ширину корпуса и разницу глубины парных суставов."""

    points = np.asarray(landmarks)

    if points.ndim != 2 or points.shape[0] < 25 or points.shape[1] < 4:
        return None

    if frame_shape is None or len(frame_shape) < 2:
        return None

    height, width = frame_shape[:2]

    indices = [11, 12, 23, 24]
    joints = points[indices]

    if not np.all(np.isfinite(joints)):
        return None

    if np.min(joints[:, 3]) < 0.6:
        return None

    left_shoulder, right_shoulder, left_hip, right_hip = joints

    shoulder_width = abs(
        left_shoulder[0] - right_shoulder[0]
    ) * width

    hip_width = abs(
        left_hip[0] - right_hip[0]
    ) * width

    shoulder_depth = abs(
        left_shoulder[2] - right_shoulder[2]
    ) * width

    hip_depth = abs(
        left_hip[2] - right_hip[2]
    ) * width

    shoulder_center_y = (
        left_shoulder[1] + right_shoulder[1]
    ) / 2

    hip_center_y = (
        left_hip[1] + right_hip[1]
    ) / 2

    torso_height = abs(
        shoulder_center_y - hip_center_y
    ) * height

    if torso_height < 1:
        return None

    width_ratio = (
        shoulder_width + hip_width
    ) / (2 * torso_height)

    depth_ratio = (
        shoulder_depth + hip_depth
    ) / (2 * torso_height)

    return SquatViewpointFeatures(
        width_ratio=float(width_ratio),
        depth_ratio=float(depth_ratio),
    )


def normalize_score(value):
    """Ограничивает оценку диапазоном от нуля до единицы."""

    return float(np.clip(value, 0.0, 1.0))
