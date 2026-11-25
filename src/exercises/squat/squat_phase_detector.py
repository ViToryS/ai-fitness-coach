
from src.exercises.base.phase import ExercisePhase
from src.exercises.base.phase_detector import PhaseDetector
from src.exercises.squat.phase.squat_phase_detector import (
    SquatPhaseDetector as SquatPhaseAlgorithm,
)


class SquatPhaseDetector(PhaseDetector):
    """Адаптирует алгоритм определения фаз приседаний к общей архитектуре."""

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
        self.detector = SquatPhaseAlgorithm()

    def update(self, landmarks) -> ExercisePhase | None:
        phase = self.detector.update(landmarks)

        if phase == SquatPhaseAlgorithm.NO_POSE:
            return None

        return self.PHASES.get(phase)

    def reset(self):
        self.detector.reset()
