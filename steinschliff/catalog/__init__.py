"""Домен каталога структур.

Задача домена:
- выбирать сервисы по фильтру (по ключу директории или по "видимому" имени из `_meta.yaml`)
- фильтровать структуры по condition

CLI и генератор должны быть тонкими обвязками поверх этой логики.
"""

from .selection import (
    build_service_name_to_key,
    filter_services_by_condition,
    select_services,
)

__all__ = [
    "build_service_name_to_key",
    "filter_services_by_condition",
    "select_services",
]
