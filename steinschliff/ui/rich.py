"""
Консольные UI-утилиты (Rich).

Почему:
    Держим форматирование/вывод отдельно от доменной логики и I/O.
"""

import logging

from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger("steinschliff.ui")
console = Console()


def print_kv_panel(title: str, rows: list[tuple[str, str]], border_style: str = "cyan") -> None:
    """Выводит ключ-значение в виде компактной таблицы в панели."""
    table = Table.grid(padding=(0, 1))
    for key, value in rows:
        table.add_row(f"[bold]{key}[/]:", f"[cyan]{value}[/]")
    console.print(Panel.fit(table, title=title, border_style=border_style))


def print_items_panel(title: str, items: list[str], border_style: str = "yellow") -> None:
    """Выводит список строк в виде таблицы в панели."""
    table = Table(show_header=False, box=None)
    table.add_column("Элемент")
    for item in items:
        table.add_row(item)
    console.print(Panel.fit(table, title=title, border_style=border_style))


def print_validation_errors(err: ValidationError, file_path: str) -> None:
    """Печатает ошибки валидации в виде таблицы Rich."""
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
    """Выводит сводку по результатам валидации YAML-файлов."""
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
