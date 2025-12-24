"""Консольные UI-утилиты (Rich).

Модуль отвечает только за отображение (таблицы/панели) и не должен содержать
доменной логики. Это упрощает тестирование и переиспользование.
"""

import logging

from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger("steinschliff.ui")
console = Console()


def print_kv_panel(title: str, rows: list[tuple[str, str]], border_style: str = "cyan") -> None:
    """Вывести пары ключ-значение в панели.

    Args:
        title: Заголовок панели.
        rows: Список пар `(key, value)`.
        border_style: Цвет рамки панели.
    """
    table = Table.grid(padding=(0, 1))
    for key, value in rows:
        table.add_row(f"[bold]{key}[/]:", f"[cyan]{value}[/]")
    console.print(Panel.fit(table, title=title, border_style=border_style))


def print_items_panel(title: str, items: list[str], border_style: str = "yellow") -> None:
    """Вывести список строк в панели.

    Args:
        title: Заголовок панели.
        items: Список строк.
        border_style: Цвет рамки панели.
    """
    table = Table(show_header=False, box=None)
    table.add_column("Элемент")
    for item in items:
        table.add_row(item)
    console.print(Panel.fit(table, title=title, border_style=border_style))


def print_validation_errors(err: ValidationError, file_path: str) -> None:
    """Показать ошибки валидации (Pydantic) в виде таблицы.

    Args:
        err: Ошибка валидации Pydantic.
        file_path: Путь к файлу, в котором произошла ошибка.
    """
    errors = err.errors()

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Поле")
    table.add_column("Тип")
    table.add_column("Текст")

    for error in errors:
        loc = " -> ".join([str(loc_part) for loc_part in error.get("loc", [])])
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        table.add_row(f"[bold]{loc}[/]", f"[magenta]{error_type}[/]", f"[red]{msg}[/]")

    console.print(Panel.fit(table, title=f"Ошибки валидации в файле: {file_path}", border_style="red"))


def print_validation_summary(valid_files: int, error_files: int, warning_files: int) -> None:
    """Показать сводку по валидации YAML-файлов.

    Note:
        Сводка показывается только если логгер `steinschliff.ui` включён на уровне INFO.

    Args:
        valid_files: Количество валидных файлов.
        error_files: Количество файлов с ошибками (не пригодны).
        warning_files: Количество файлов с предупреждениями (частичная валидация).
    """
    # Сохраняем прежнее поведение: сводка показывается только при INFO.
    if not logger.isEnabledFor(logging.INFO):
        return

    total = valid_files + error_files + warning_files
    valid_percent = (valid_files / total * 100) if total else 0
    warning_percent = (warning_files / total * 100) if total else 0
    error_percent = (error_files / total * 100) if total else 0

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Статус")
    table.add_column("Кол-во", justify="right")
    table.add_column("Доля", justify="right")

    table.add_row("[green]✓ Успешно[/]", str(valid_files), f"{valid_percent:.1f}%")
    table.add_row("[yellow]⚠ Предупреждения[/]", str(warning_files), f"{warning_percent:.1f}%")
    table.add_row("[red]✗ Ошибки[/]", str(error_files), f"{error_percent:.1f}%")

    console.print(Panel.fit(table, title="Результаты валидации YAML-файлов", border_style="cyan"))
