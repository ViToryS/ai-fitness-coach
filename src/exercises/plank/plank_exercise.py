
from src.exercises.base.exercise import Exercise
from src.exercises.base.exercise_analyzer import ExerciseAnalyzer

from src.exercises.plank.plank_phase_analyzer import PlankPhaseAnalyzer
from src.exercises.plank.plank_phase_detector import PlankPhaseDetector

from src.exercises.plank.plank_viewpoint_analyzer import (
    PlankViewpointAnalyzer,
)
from src.exercises.plank.plank_viewpoint_detector import (
    PlankViewpointDetector,
)

from src.models.viewpoint import Viewpoint


class PlankExercise(Exercise):

    @property
    def id(self) -> str:
        return "plank"

    @property
    def name(self) -> str:
        return "Планка на предплечьях"

    @property
    def description(self) -> str:
        return "Контроль статического положения в планке."

    @property
    def supported_viewpoints(self) -> list[Viewpoint]:
        return [
            Viewpoint.SIDE,
            Viewpoint.DIAGONAL,
            Viewpoint.FRONT,
        ]

    def create_analyzer(self) -> ExerciseAnalyzer:
        return ExerciseAnalyzer(
            analyzers=[
                PlankPhaseAnalyzer(
                    detector=PlankPhaseDetector(),
                ),
                PlankViewpointAnalyzer(
                    detector=PlankViewpointDetector(),
                ),
            ]
        )
