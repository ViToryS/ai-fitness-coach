from exercises.base.phase_detector import PhaseDetector
from src.exercises.base.exercise import Exercise
from src.exercises.squat.squat_phase_detector import SquatPhaseDetector
from src.models.viewpoint import Viewpoint


class SquatExercise(Exercise):
    """Описывает упражнение приседания и его настройки."""

    @property
    def name(self) -> str:
        return "Приседания"

    @property
    def supported_viewpoints(self) -> list[Viewpoint]:
        return [
            Viewpoint.FRONT,
            Viewpoint.SIDE,
            Viewpoint.DIAGONAL
        ]

    def create_phase_detector(self) -> PhaseDetector:
        return SquatPhaseDetector()
