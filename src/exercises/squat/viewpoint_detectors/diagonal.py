
from src.exercises.squat.viewpoint_detectors.base import (
    SquatViewpointCandidate,
    SquatViewpointFeatures,
    normalize_score,
)


class DiagonalViewpointDetector(SquatViewpointCandidate):
    """Оценивает признаки диагонального ракурса приседания."""

    def score(self, features: SquatViewpointFeatures) -> float:
        width_score = normalize_score(
            1.0 - abs(features.width_ratio - 0.38) / 0.22
        )

        depth_score = normalize_score(
            features.depth_ratio / 0.8
        )

        return width_score * depth_score
