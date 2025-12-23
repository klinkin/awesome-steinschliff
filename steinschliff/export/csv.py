"""Экспорт структур в CSV.

Функции этого модуля не читают YAML напрямую: на вход подаются уже
сформированные `StructureInfo`.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from typing import Any

from steinschliff.formatters import format_list_for_display, format_temperature_range
from steinschliff.models import StructureInfo
from steinschliff.snow_conditions import get_name_ru


def _format_condition(condition: str | None) -> str:
    """Отформатировать условие снега для CSV.

    Args:
        condition: Канонический ключ условия (например, `blue`) или `None`.

    Returns:
        Русское название условия (`name_ru`), либо `Key.capitalize()`, либо `""` для пустого входа.
    """
    if not condition:
        return ""

    key = condition.strip().lower()
    if not key:
        return ""

    name_ru = get_name_ru(key)
    return name_ru or key.capitalize()


def export_structures_csv_string(
    *,
    services: dict[str, list[StructureInfo]],
    sort_key: Callable[[StructureInfo], Any] | None = None,
) -> str:
    """Экспортировать структуры в CSV и вернуть содержимое как строку.

    Args:
        services: Маппинг `service_key -> list[StructureInfo]`.
        sort_key: Необязательная функция ключа сортировки внутри сервиса.

    Returns:
        CSV в виде строки (с заголовком).
    """
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)

    writer.writerow(["Сервис", "Имя", "Тип снега", "Условия", "Температура", "Похожие"])

    for service_key, service_items in services.items():
        sorted_items = sorted(service_items, key=sort_key) if sort_key is not None else service_items

        for s in sorted_items:
            temp_str = format_temperature_range(s.temperature)
            similars_str = format_list_for_display(s.similars)
            condition_str = _format_condition(s.condition)

            writer.writerow(
                [
                    (s.service.name if s.service and s.service.name else service_key) or service_key,
                    str(s.name),
                    s.snow_type or "",
                    condition_str,
                    temp_str,
                    similars_str,
                ]
            )

    return csv_buffer.getvalue()
