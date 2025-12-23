"""Точка входа для CLI.

Почему отдельный entry point:
    Консольный скрипт (в `pyproject.toml`) должен указывать на вызываемую функцию.
    Это позволяет также поддерживать запуск через `python -m steinschliff`.
"""

from __future__ import annotations

from steinschliff.cli.app import app


def entry_point() -> None:
    """Запускает Typer-приложение."""
    app()
