"""Исключения проекта."""

from __future__ import annotations


class SteinschliffUserError(Exception):
    """Ожидаемая ошибка пользователя (валидные сценарии CLI без трейсбэка)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
