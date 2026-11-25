from src.exercises.base.exercise import Exercise
from src.exercises.base.exercise_analyzer import ExerciseAnalyzer
from src.exercises.squat.squat_phase_analyzer import SquatPhaseAnalyzer
from src.exercises.squat.squat_phase_detector import SquatPhaseDetector
from src.exercises.squat.squat_viewpoint_analyzer import SquatViewpointAnalyzer
from src.exercises.squat.squat_viewpoint_detector import SquatViewpointDetector
from src.models.viewpoint import Viewpoint


class SquatExercise(Exercise):

    @property
    def id(self) -> str:
        return "squat"

    @property
    def name(self) -> str:
        return "Приседания"

    @property
    def description(self) -> str:
        return "Анализ техники выполнения приседаний."

    @property
    def supported_viewpoints(self) -> list[Viewpoint]:
        return [
            Viewpoint.FRONT,
            Viewpoint.SIDE,
            Viewpoint.DIAGONAL,
        ]

    def create_analyzer(self) -> ExerciseAnalyzer:
        return ExerciseAnalyzer(
            analyzers=[
                SquatPhaseAnalyzer(
                    detector=SquatPhaseDetector(),
                ),
                SquatViewpointAnalyzer(
                    detector=SquatViewpointDetector(),
                ),
            ]
        )