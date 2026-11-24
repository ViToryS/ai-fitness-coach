
from src.exercises.squat.viewpoint_detectors.base import (
    SquatViewpointCandidate,
    SquatViewpointFeatures,
    normalize_score,
)


class FrontViewpointDetector(SquatViewpointCandidate):
    """Оценивает признаки переднего ракурса приседания."""

    def score(self, features: SquatViewpointFeatures) -> float:
        width_score = normalize_score(
            (features.width_ratio - 0.25) / 0.30
        )

        depth_score = normalize_score(
            1.0 - features.depth_ratio / 0.8
        )

        return width_score * depth_score
