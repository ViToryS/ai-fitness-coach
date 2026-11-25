
from src.exercises.push_up.viewpoint_detectors.base import (
    PushUpViewpointCandidate,
    PushUpViewpointFeatures,
    normalize_score,
)


class SideViewpointDetector(PushUpViewpointCandidate):

    def score(self, features: PushUpViewpointFeatures) -> float:
        return normalize_score(
            (0.45 - features.horizontal_ratio) / 0.35
        )
