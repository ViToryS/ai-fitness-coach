from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROFILE_SCHEMA: dict[str, dict[str, Any]] = {
    "name": {"type": str, "required": True},
    "version": {"type": int, "required": True, "min": 1},
    "description": {"type": str, "required": False},
    "joints": {
        "type": list,
        "required": True,
        "item_type": str,
    },
    "visibility_threshold": {
        "type": float,
        "required": True,
        "min": 0.0,
        "max": 1.0,
    },
    "smoothing_alpha": {
        "type": float,
        "required": True,
        "min": 0.0,
        "max": 1.0,
    },
    "target_angles": {
        "type": dict,
        "required": False,
        "value_type": (int, float),
    },
}


class ProfileValidationError(ValueError):
    """Ошибка валидации профиля."""


def load_profile(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ProfileValidationError(f"Файл профиля не найден: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ProfileValidationError(f"Некорректный JSON: {exc}") from exc

    _validate(data)
    return data


def _validate(data: dict[str, Any]):
    if not isinstance(data, dict):
        raise ProfileValidationError("Корень профиля должен быть объектом JSON.")

    errors: list[str] = []

    for field_name, rules in PROFILE_SCHEMA.items():
        value = data.get(field_name)
        required = rules.get("required", False)

        if value is None:
            if required:
                errors.append(f"Отсутствует обязательное поле '{field_name}'.")
            continue

        expected_type = rules["type"]
        if not isinstance(value, expected_type):
            errors.append(
                f"Поле '{field_name}': ожидается {expected_type.__name__}, "
                f"получено {type(value).__name__}."
            )
            continue

        if expected_type in (int, float):
            min_val = rules.get("min")
            max_val = rules.get("max")
            if min_val is not None and value < min_val:
                errors.append(
                    f"Поле '{field_name}': значение {value} меньше {min_val}."
                )
            if max_val is not None and value > max_val:
                errors.append(
                    f"Поле '{field_name}': значение {value} больше {max_val}."
                )

        if expected_type is list and "item_type" in rules:
            item_type = rules["item_type"]
            for idx, item in enumerate(value):
                if not isinstance(item, item_type):
                    errors.append(
                        f"Поле '{field_name}[{idx}]': ожидается "
                        f"{item_type.__name__}, получено {type(item).__name__}."
                    )

        if expected_type is dict and "value_type" in rules:
            value_type = rules["value_type"]
            for key, val in value.items():
                if not isinstance(val, value_type):
                    errors.append(
                        f"Поле '{field_name}.{key}': ожидается "
                        f"{value_type}, получено {type(val).__name__}."
                    )

    if errors:
        raise ProfileValidationError(
            "Профиль содержит ошибки:\n" + "\n".join(f"  • {e}" for e in errors)
        )