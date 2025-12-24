"""Единое место для вычисления путей проекта.

Задача модуля:
- убрать разрозненные вычисления путей через `__file__` по всему проекту
- нормализовать работу с путями через `pathlib.Path`

Важно:
    Мы допускаем использование `__file__` только здесь, чтобы остальной код работал
    с готовыми функциями/Path и не дублировал логику.
"""

from __future__ import annotations

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

    Поведение близко к классическому `relpath`, но реализовано через `pathlib`, чтобы не использовать `os.path`.

    Args:
        path: Путь, который нужно сделать относительным.
        start: База для относительного пути.

    Returns:
        Относительный путь как `Path`.
    """
    p_abs = Path(path).resolve()
    s_abs = Path(start).resolve()

    p_parts = p_abs.parts
    s_parts = s_abs.parts

    common_len = 0
    for a, b in zip(p_parts, s_parts, strict=False):
        if a != b:
            break
        common_len += 1

    up_levels = [".."] * (len(s_parts) - common_len)
    down_parts = list(p_parts[common_len:])
    rel_parts = [*up_levels, *down_parts]

    return Path(*rel_parts) if rel_parts else Path()
