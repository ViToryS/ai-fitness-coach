from src.exercises.base.phase import ExercisePhase
from src.exercises.base.phase_detector import PhaseDetector
from src.exercises.push_up.phase.push_up_phase_algorithm import (
    PushUpPhaseAlgorithm,
)


class PushUpPhaseDetector(PhaseDetector):

    PHASES = {
        PushUpPhaseAlgorithm.READY: ExercisePhase(
            "ready", "Исходное положение"
        ),
        PushUpPhaseAlgorithm.DESCENT: ExercisePhase(
            "descent", "Опускание"
        ),
        PushUpPhaseAlgorithm.BOTTOM: ExercisePhase(
            "bottom", "Нижняя точка"
        ),
        PushUpPhaseAlgorithm.ASCENT: ExercisePhase(
            "ascent", "Подъём"
        ),
    }

    def __init__(self):
        self._algorithm = PushUpPhaseAlgorithm()

    def update(self, landmarks) -> ExercisePhase | None:
        phase = self._algorithm.update(landmarks)

        if phase == PushUpPhaseAlgorithm.NO_POSE:
            return None

        return self.PHASES.get(phase)

    def reset(self):
        self._algorithm.reset()