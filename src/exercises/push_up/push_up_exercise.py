from src.exercises.base.exercise import Exercise
from src.exercises.base.exercise_analyzer import ExerciseAnalyzer
from src.exercises.push_up.push_up_phase_analyzer import PushUpPhaseAnalyzer
from src.exercises.push_up.push_up_phase_detector import PushUpPhaseDetector
from src.exercises.push_up.push_up_viewpoint_analyzer import PushUpViewpointAnalyzer
from src.exercises.push_up.push_up_viewpoint_detector import PushUpViewpointDetector
from src.models.viewpoint import Viewpoint


class PushUpExercise(Exercise):

    @property
    def id(self) -> str:
        return "push_up"

    @property
    def name(self) -> str:
        return "Отжимания"

    @property
    def description(self) -> str:
        return "Определение фаз выполнения отжиманий."

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
                PushUpPhaseAnalyzer(
                    detector=PushUpPhaseDetector(),
                ),
                PushUpViewpointAnalyzer(
                    detector=PushUpViewpointDetector(),
                ),
            ]
        )