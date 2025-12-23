"""CLI пакет проекта.

Entry-point в `pyproject.toml` указывает на `scripts.cli:app`, поэтому здесь
экспортируем объект `app`.
"""

from .app import app

__all__ = ["app"]
