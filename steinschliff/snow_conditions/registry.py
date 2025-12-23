"""Реестр snow conditions (условий снега).

Модуль загружает `snow_conditions/*.yaml` из репозитория и предоставляет:
- список допустимых ключей
- поиск информации по ключу
- нормализацию пользовательского ввода (CLI)

Кэширование:
    Данные YAML и таблица нормализации кэшируются через `functools.lru_cache`.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from steinschliff.paths import project_root, snow_conditions_dir

DEFAULT_SNOW_CONDITION_KEYS = ["red", "blue", "violet", "orange", "green", "yellow", "pink", "brown"]

# Поддержка ввода по русским названиям цветов (историческое поведение CLI).
_COLOR_RU_TO_KEY: dict[str, str] = {
    "красный": "red",
    "синий": "blue",
    "фиолетовый": "violet",
    "оранжевый": "orange",
    "зелёный": "green",
    "зеленый": "green",
    "жёлтый": "yellow",
    "желтый": "yellow",
    "розовый": "pink",
    "коричневый": "brown",
}


def _project_root() -> Path:
    """Получить корень репозитория (через `steinschliff.paths`)."""
    return project_root()


def _snow_conditions_dir() -> Path:
    """Получить директорию `snow_conditions/` (через `steinschliff.paths`)."""
    return snow_conditions_dir()


def _safe_load_yaml(path: Path) -> dict[str, Any] | None:
    """Безопасно прочитать YAML-файл как dict.

    Args:
        path: Путь к YAML-файлу.

    Returns:
        Dict с данными или `None` при ошибке чтения/парсинга или неверном типе корня.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else None
    except (OSError, yaml.YAMLError):
        return None


@functools.lru_cache(maxsize=1)
def _load_registry() -> dict[str, dict[str, Any]]:
    """Загрузить все условия из `snow_conditions/*.yaml` и закэшировать.

    Returns:
        Реестр `key -> data`.
    """
    root = _snow_conditions_dir()
    if not root.exists():
        return {}

    registry: dict[str, dict[str, Any]] = {}
    for yaml_file in root.glob("*.yaml"):
        data = _safe_load_yaml(yaml_file)
        if not data:
            continue

        key = str(data.get("key", yaml_file.stem)).strip().lower()
        if not key:
            continue

        registry[key] = data

    return registry


@functools.lru_cache(maxsize=1)
def _build_lookup() -> dict[str, str]:
    """Построить маппинг “вариант ввода” → канонический `key`.

    Returns:
        Словарь, в который входят:
        - `red/blue/...` ключи
        - русские названия цветов
        - `name`, `name_ru`, `synonyms`, `synonyms_ru` из YAML-файлов
    """
    lookup: dict[str, str] = {}

    # Ключи и русские названия цветов:
    for ru, key in _COLOR_RU_TO_KEY.items():
        lookup[ru] = key
    for key in get_valid_keys():
        lookup[key] = key

    # name_ru / name / synonyms / synonyms_ru:
    for key, data in _load_registry().items():
        name = str(data.get("name", "")).strip().lower()
        name_ru = str(data.get("name_ru", "")).strip().lower()

        if name:
            lookup[name] = key
        if name_ru:
            lookup[name_ru] = key

        for field in ("synonyms", "synonyms_ru"):
            values = data.get(field, [])
            if isinstance(values, list):
                for v in values:
                    vv = str(v).strip().lower()
                    if vv:
                        lookup[vv] = key

    return lookup


def get_valid_keys() -> list[str]:
    """Получить список допустимых ключей `condition`.

    Returns:
        Список ключей. Если YAML-реестр пуст, возвращает `DEFAULT_SNOW_CONDITION_KEYS`.
    """
    keys = sorted(_load_registry().keys())
    return keys if keys else DEFAULT_SNOW_CONDITION_KEYS


def get_condition_info(key: str) -> dict[str, Any] | None:
    """Получить данные snow condition по ключу.

    Args:
        key: Канонический ключ (например, `blue`).

    Returns:
        Словарь из `snow_conditions/<key>.yaml` или `None`, если ключ неизвестен/пуст.
    """
    if not key:
        return None
    return _load_registry().get(key.strip().lower())


def get_name_ru(key: str) -> str | None:
    """Получить русское название условия по ключу.

    Args:
        key: Канонический ключ.

    Returns:
        Значение `name_ru` или `None`.
    """
    info = get_condition_info(key)
    if not info:
        return None
    name_ru = info.get("name_ru")
    return str(name_ru) if name_ru else None


def normalize_condition_input(condition_input: str) -> str:
    """Нормализовать пользовательский ввод условия (для CLI/фильтров).

    Поддерживает:
    - key (red/blue/…)
    - русские названия цветов (Красный/Зелёный/…)
    - name/name_ru/synonyms/synonyms_ru из файлов `snow_conditions/*.yaml`

    Если не распознано — возвращает приведённую к lower строку (как было ранее).
    """
    if not condition_input:
        return ""

    s = condition_input.strip().lower()
    if not s:
        return ""

    return _build_lookup().get(s, s)
