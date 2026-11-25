
from src.exercises.base.phase import ExercisePhase
from src.exercises.base.phase_detector import PhaseDetector
from src.exercises.plank.phase.plank_phase_algorithm import (
    PlankPhaseAlgorithm,
)


class PlankPhaseDetector(PhaseDetector):

    PHASES = {
        PlankPhaseAlgorithm.READY: ExercisePhase(
            "ready",
            "Исходное положение",
        ),
        PlankPhaseAlgorithm.HOLD: ExercisePhase(
            "hold",
            "Удержание планки",
        ),
    }

    def __init__(self):
        self._algorithm = PlankPhaseAlgorithm()

    def update(self, landmarks) -> ExercisePhase | None:
        phase = self._algorithm.update(landmarks)

        if phase == PlankPhaseAlgorithm.NO_POSE:
            return None

        return self.PHASES.get(phase)

    def reset(self):
        self._algorithm.reset()
