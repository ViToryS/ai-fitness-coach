from dataclasses import dataclass


@dataclass(frozen=True)
class ExercisePhase:
    """Хранит код и название фазы упражнения."""

    code: str
    name: str