from __future__ import annotations

import functools
from collections.abc import Callable

import rich.panel
import typer
from rich import print

from steinschliff.exceptions import SteinschliffUserError


def handle_user_errors[T, **P](function: Callable[P, T]) -> Callable[P, T]:
    """Декоратор для CLI: показывает дружелюбные сообщения без трейсбэка для ожидаемых ошибок."""

    @functools.wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return function(*args, **kwargs)
        except SteinschliffUserError as e:
            print(
                rich.panel.Panel(
                    e.message,
                    title="[bold red]Ошибка[/bold red]",
                    title_align="left",
                    border_style="bold red",
                )
            )
            raise typer.Exit(code=1) from e

    return wrapper
