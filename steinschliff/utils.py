"""
Вспомогательные функции для Steinschliff.

Важно:
    Исторически модуль разросся и смешал несколько доменов (UI, I/O, логирование).
    Новая структура:
      - `steinschliff/ui/` — Rich-вывод
      - `steinschliff/io/` — чтение YAML и метаданных
      - `steinschliff/logging.py` — настройка логов

    Этот модуль оставлен как **совместимый фасад** для старых импортов.
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from steinschliff.io.yaml import find_yaml_files, read_service_metadata, read_yaml_file
from steinschliff.logging import setup_logging
from steinschliff.ui.rich import (
    console,
    print_items_panel,
    print_kv_panel,
    print_validation_errors,
    print_validation_summary,
)

# Константы для цветного вывода в терминал (используются в format_validation_error)
RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
BOLD = "\033[1m"

logger = logging.getLogger("steinschliff.utils")


def format_validation_error(err: ValidationError, file_path: str) -> str:
    """
    Форматирует ошибку валидации Pydantic в удобочитаемый текст.

    Args:
        err: Объект ошибки ValidationError
        file_path: Путь к файлу с ошибкой

    Returns:
        Отформатированная строка с подробным описанием ошибок
    """
    errors = err.errors()
    report = [f"{RED}{BOLD}ОШИБКИ ВАЛИДАЦИИ В ФАЙЛЕ: {file_path}{RESET}"]
    report.append(f"{YELLOW}{'=' * 50}{RESET}")

    for i, error in enumerate(errors, 1):
        loc = " -> ".join([str(loc_part) for loc_part in error.get("loc", [])])
        error_type = error.get("type", "")
        msg = error.get("msg", "")

        report.append(f"{BOLD}Ошибка #{i}:{RESET}")
        report.append(f"  {CYAN}Поле:{RESET}  {BOLD}{loc}{RESET}")
        report.append(f"  {CYAN}Тип:{RESET}   {MAGENTA}{error_type}{RESET}")
        report.append(f"  {CYAN}Текст:{RESET} {RED}{msg}{RESET}")
        report.append(f"{YELLOW}{'-' * 50}{RESET}")

    return "\n".join(report)


# Экспортируем публичный API модуля (совместимость со старыми импортами).
__all__ = [
    "console",
    "find_yaml_files",
    "format_validation_error",
    "print_items_panel",
    "print_kv_panel",
    "print_validation_errors",
    "print_validation_summary",
    "read_service_metadata",
    "read_yaml_file",
    "setup_logging",
]
