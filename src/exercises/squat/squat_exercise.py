
from src.exercises.base.exercise import Exercise
from src.exercises.base.phase_detector import PhaseDetector
from src.exercises.base.viewpoint_detector import ViewpointDetector
from src.exercises.squat.squat_phase_detector import SquatPhaseDetector
from src.exercises.squat.squat_viewpoint_detector import SquatViewpointDetector
from src.models.viewpoint import Viewpoint


class SquatExercise(Exercise):
    """Описывает приседание и его настройки анализа."""

    @property
    def name(self) -> str:
        return "Приседания"

    @property
    def supported_viewpoints(self) -> list[Viewpoint]:
        return [
            Viewpoint.FRONT,
            Viewpoint.SIDE,
            Viewpoint.DIAGONAL,
        ]

    def create_phase_detector(self) -> PhaseDetector:
        return SquatPhaseDetector()

    def create_viewpoint_detector(self) -> ViewpointDetector:
        return SquatViewpointDetector()
