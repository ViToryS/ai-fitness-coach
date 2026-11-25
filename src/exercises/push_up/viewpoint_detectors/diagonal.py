
from src.exercises.push_up.viewpoint_detectors.base import (
    PushUpViewpointCandidate,
    PushUpViewpointFeatures,
    normalize_score,
)


class DiagonalViewpointDetector(PushUpViewpointCandidate):

    def score(self, features: PushUpViewpointFeatures) -> float:
        return normalize_score(
            1.0 - abs(features.horizontal_ratio - 0.5) / 0.35
        )
