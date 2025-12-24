"""
UI слой проекта: функции, связанные с выводом в консоль (Rich).
"""

from .rich import (
    console,
    print_items_panel,
    print_kv_panel,
    print_validation_errors,
    print_validation_summary,
)

__all__ = [
    "console",
    "print_items_panel",
    "print_kv_panel",
    "print_validation_errors",
    "print_validation_summary",
]
