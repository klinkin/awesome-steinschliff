"""Единое место для вычисления путей проекта.

Задача модуля:
- убрать разрозненные вычисления путей через `__file__` по всему проекту
- нормализовать работу с путями через `pathlib.Path`

Важно:
    Мы допускаем использование `__file__` только здесь, чтобы остальной код работал
    с готовыми функциями/Path и не дублировал логику.
"""

from __future__ import annotations

import os
from pathlib import Path


def package_root() -> Path:
    """Получить директорию пакета `steinschliff/`.

    Returns:
        Путь к директории пакета.
    """

    return Path(__file__).resolve().parent


def project_root() -> Path:
    """Получить корень репозитория (директория над `steinschliff/`).

    Returns:
        Путь к корню репозитория.
    """

    return package_root().parent


def templates_dir() -> Path:
    """Получить директорию шаблонов Jinja2 внутри пакета."""

    return package_root() / "templates"


def translations_dir() -> Path:
    """Получить директорию переводов Babel внутри пакета."""

    return package_root() / "translations"


def snow_conditions_dir() -> Path:
    """Получить директорию `snow_conditions/` в корне репозитория."""

    return project_root() / "snow_conditions"


def relpath(path: str | Path, start: str | Path) -> Path:
    """Построить относительный путь `path` относительно `start`.

    Это тонкая обёртка над `os.path.relpath`, чтобы не размазывать `os.path` по коду.

    Args:
        path: Путь, который нужно сделать относительным.
        start: База для относительного пути.

    Returns:
        Относительный путь как `Path`.
    """

    return Path(os.path.relpath(str(path), str(start)))
