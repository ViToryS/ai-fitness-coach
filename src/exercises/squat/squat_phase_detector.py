
from src.core.phase_detector import SquatPhaseDetector as CoreSquatPhaseDetector
from src.exercises.base.phase import ExercisePhase
from src.exercises.base.phase_detector import PhaseDetector


class SquatPhaseDetector(PhaseDetector):
    """Адаптирует существующий детектор приседаний к общей архитектуре."""

    PHASES = {
        "Исходное положение": ExercisePhase("ready", "Исходное положение"),
        "Опускание": ExercisePhase("descent", "Опускание"),
        "Нижняя точка": ExercisePhase("bottom", "Нижняя точка"),
        "Подъём": ExercisePhase("ascent", "Подъём"),
        "Завершение": ExercisePhase("complete", "Завершение"),
    }

    def __init__(self):
        self.detector = CoreSquatPhaseDetector()

    def update(self, landmarks) -> ExercisePhase | None:
        phase = self.detector.update(landmarks)

        if phase == CoreSquatPhaseDetector.NO_POSE:
            return None

        return self.PHASES.get(phase)

    def reset(self):
        self.detector.reset()
