"""Домен `snow_conditions`.

Единый источник истины для:
- списка допустимых `condition` ключей (red/blue/…)
- локализованных названий `name_ru`
- нормализации пользовательского ввода (ключи, русские названия цветов, синонимы)
"""

from .registry import (
    DEFAULT_SNOW_CONDITION_KEYS,
    get_condition_info,
    get_name_ru,
    get_valid_keys,
    normalize_condition_input,
)

__all__ = [
    "DEFAULT_SNOW_CONDITION_KEYS",
    "get_condition_info",
    "get_name_ru",
    "get_valid_keys",
    "normalize_condition_input",
]
