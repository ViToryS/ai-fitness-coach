from dataclasses import dataclass

from src.exercises.base.phase import ExercisePhase
from src.models.viewpoint import Viewpoint


@dataclass(frozen=True)
class PhaseChanged:
    phase: ExercisePhase


@dataclass(frozen=True)
class ViewpointChanged:
    viewpoint: Viewpoint
    count: int


AnalysisEvent = PhaseChanged | ViewpointChanged