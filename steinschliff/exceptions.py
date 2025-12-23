"""Исключения проекта."""

from __future__ import annotations


class SteinschliffUserError(Exception):
    """Ожидаемая ошибка пользователя (валидные сценарии CLI без трейсбэка)."""

    def __init__(self, message: str) -> None:
        """Создать ошибку с пользовательским сообщением.

        Args:
            message: Сообщение, которое можно безопасно показывать пользователю.
        """
        super().__init__(message)
        self.message = message
