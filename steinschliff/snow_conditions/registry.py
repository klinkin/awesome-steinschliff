from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

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
    # steinschliff/snow_conditions/registry.py -> steinschliff -> repo root
    return Path(__file__).resolve().parents[2]


def _snow_conditions_dir() -> Path:
    return _project_root() / "snow_conditions"


def _safe_load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else None
    except (OSError, yaml.YAMLError):
        return None


@functools.lru_cache(maxsize=1)
def _load_registry() -> dict[str, dict[str, Any]]:
    """Загружает все snow_conditions из `snow_conditions/*.yaml` и кеширует."""
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
    """Строит маппинг 'разные варианты ввода' -> канонический key."""
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
    """Возвращает список допустимых ключей condition."""
    keys = sorted(_load_registry().keys())
    return keys if keys else DEFAULT_SNOW_CONDITION_KEYS


def get_condition_info(key: str) -> dict[str, Any] | None:
    """Возвращает словарь из `snow_conditions/<key>.yaml` или None."""
    if not key:
        return None
    return _load_registry().get(key.strip().lower())


def get_name_ru(key: str) -> str | None:
    """Возвращает `name_ru` для указанного snow condition key."""
    info = get_condition_info(key)
    if not info:
        return None
    name_ru = info.get("name_ru")
    return str(name_ru) if name_ru else None


def normalize_condition_input(condition_input: str) -> str:
    """Нормализует пользовательский ввод для фильтров CLI.

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
