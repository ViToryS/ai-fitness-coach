
from collections.abc import Callable

from src.exercises.base.exercise import Exercise


class ExerciseRegistry:
    """Реестр доступных упражнений."""

    def __init__(self):
        self._factories: dict[str, Callable[[], Exercise]] = {}

    def register(self, exercise_factory: Callable[[], Exercise]) -> None:
        """
        Регистрирует фабрику упражнения.

        В качестве фабрики можно передать класс упражнения,
        например SquatExercise.
        """
        exercise = exercise_factory()
        exercise_id = exercise.id

        if not exercise_id or not exercise_id.strip():
            raise ValueError("У упражнения должен быть непустой id.")

        if exercise_id in self._factories:
            raise ValueError(
                f"Упражнение с id '{exercise_id}' уже зарегистрировано."
            )

        self._factories[exercise_id] = exercise_factory

    def get(self, exercise_id: str) -> Exercise:
        """Создаёт и возвращает упражнение по его id."""
        factory = self._factories.get(exercise_id)

        if factory is None:
            available = ", ".join(sorted(self._factories)) or "нет"

            raise KeyError(
                f"Упражнение '{exercise_id}' не найдено. "
                f"Зарегистрированные упражнения: {available}."
            )

        return factory()

    def list_exercises(self) -> list[Exercise]:
        """Возвращает экземпляры всех зарегистрированных упражнений."""
        return [
            factory()
            for factory in self._factories.values()
        ]

    def __contains__(self, exercise_id: str) -> bool:
        return exercise_id in self._factories

    def __len__(self) -> int:
        return len(self._factories)
