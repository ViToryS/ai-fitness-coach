
from src.exercises.squat.viewpoint_detectors.base import (
    SquatViewpointCandidate,
    SquatViewpointFeatures,
    normalize_score,
)


class SideViewpointDetector(SquatViewpointCandidate):
    """Оценивает признаки бокового ракурса приседания."""

    def score(self, features: SquatViewpointFeatures) -> float:
        width_score = normalize_score(
            1.0 - features.width_ratio / 0.24
        )

        depth_score = normalize_score(
            features.depth_ratio / 0.8
        )

        return width_score * depth_score

