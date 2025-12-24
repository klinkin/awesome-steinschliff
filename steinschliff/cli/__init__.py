"""CLI пакет проекта (Typer).

Публичная точка входа для консольного скрипта — `steinschliff.cli.entry_point:entry_point`.
"""

from __future__ import annotations

from .app import app

__all__ = ["app"]
