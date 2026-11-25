
from src.exercises.base.phase import ExercisePhase
from src.exercises.base.phase_detector import PhaseDetector
from src.exercises.squat.phase.squat_phase_algorithm import (
    SquatPhaseAlgorithm,
)


class SquatPhaseDetector(PhaseDetector):
    """Адаптер алгоритма приседаний для общей архитектуры упражнений."""

    PHASES = {
        SquatPhaseAlgorithm.READY: ExercisePhase(
            "ready", "Исходное положение"
        ),
        SquatPhaseAlgorithm.DESCENT: ExercisePhase(
            "descent", "Опускание"
        ),
        SquatPhaseAlgorithm.BOTTOM: ExercisePhase(
            "bottom", "Нижняя точка"
        ),
        SquatPhaseAlgorithm.ASCENT: ExercisePhase(
            "ascent", "Подъём"
        ),
    }

    def __init__(self):
        self._algorithm = SquatPhaseAlgorithm()

    def update(self, landmarks) -> ExercisePhase | None:
        phase = self._algorithm.update(landmarks)

        if phase == SquatPhaseAlgorithm.NO_POSE:
            return None

        return self.PHASES.get(phase)

    def reset(self):
        self._algorithm.reset()
