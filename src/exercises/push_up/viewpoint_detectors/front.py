
from src.exercises.push_up.viewpoint_detectors.base import (
    PushUpViewpointCandidate,
    PushUpViewpointFeatures,
    normalize_score,
)


class FrontViewpointDetector(PushUpViewpointCandidate):

    def score(self, features: PushUpViewpointFeatures) -> float:
        return normalize_score(
            (features.horizontal_ratio - 0.55) / 0.35
        )
