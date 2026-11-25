
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PushUpViewpointFeatures:
    horizontal_ratio: float


class PushUpViewpointCandidate(ABC):

    @abstractmethod
    def score(self, features: PushUpViewpointFeatures) -> float:
        pass


def extract_push_up_features(landmarks):
    points = np.asarray(landmarks)

    if points.ndim != 2 or points.shape[0] < 25 or points.shape[1] < 4:
        return None

    indices = [11, 12, 23, 24]
    joints = points[indices]

    if not np.all(np.isfinite(joints)):
        return None

    if np.min(joints[:, 3]) < 0.6:
        return None

    left_shoulder, right_shoulder, left_hip, right_hip = joints

    horizontal_separation = np.mean([
        abs(left_shoulder[0] - right_shoulder[0]),
        abs(left_hip[0] - right_hip[0]),
    ])

    depth_separation = np.mean([
        abs(left_shoulder[2] - right_shoulder[2]),
        abs(left_hip[2] - right_hip[2]),
    ])

    total_separation = horizontal_separation + depth_separation

    if total_separation < 0.015:
        return None

    horizontal_ratio = horizontal_separation / total_separation

    return PushUpViewpointFeatures(
        horizontal_ratio=float(horizontal_ratio),
    )


def normalize_score(value):
    return float(np.clip(value, 0.0, 1.0))
