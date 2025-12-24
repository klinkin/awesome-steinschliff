from __future__ import annotations

from collections.abc import Mapping

from steinschliff.models import ServiceMetadata, StructureInfo


def build_service_name_to_key(
    *,
    services: Mapping[str, list[StructureInfo]],
    service_metadata: Mapping[str, ServiceMetadata],
) -> dict[str, str]:
    """Построить маппинг “видимое имя сервиса” → ключ сервиса (папка).

    Поддерживает:
    - ключи директории (`ramsau`)
    - `meta.name` из `_meta.yaml` (например, `Ramsau`)

    Args:
        services: Маппинг `service_key -> list[StructureInfo]`.
        service_metadata: Маппинг `service_key -> ServiceMetadata`.

    Returns:
        Словарь, где ключ — `lower()` от видимого имени, а значение — `service_key`.
    """
    mapping: dict[str, str] = {}

    for key in services:
        mapping[key.strip().lower()] = key

    for key, meta in service_metadata.items():
        visible_name = (meta.name or key).strip()
        if visible_name:
            mapping[visible_name.lower()] = key

    return mapping


def select_services(
    *,
    services: Mapping[str, list[StructureInfo]],
    service_metadata: Mapping[str, ServiceMetadata],
    service_filter: str | None,
) -> dict[str, list[StructureInfo]]:
    """Выбрать сервис(ы) по фильтру `service_filter` (или вернуть все).

    Args:
        services: Все сервисы.
        service_metadata: Метаданные сервисов (для поиска по “видимому имени”).
        service_filter: Значение фильтра (ключ директории или `meta.name`). `None`/пусто → вернуть все.

    Returns:
        Новый словарь с выбранными сервисами.

    Raises:
        ValueError: Если `service_filter` задан, но сервис не найден.
    """
    selected_services: dict[str, list[StructureInfo]] = dict(services)
    if not service_filter:
        return selected_services

    lookup = service_filter.strip().lower()
    if not lookup:
        return selected_services

    name_to_key = build_service_name_to_key(services=services, service_metadata=service_metadata)
    resolved_key = name_to_key.get(lookup)
    if resolved_key is None or resolved_key not in selected_services:
        msg = f"Сервис '{service_filter}' не найден"
        raise ValueError(msg)

    return {resolved_key: selected_services[resolved_key]}


def filter_services_by_condition(
    *,
    services: Mapping[str, list[StructureInfo]],
    condition_key: str,
) -> dict[str, list[StructureInfo]]:
    """Отфильтровать структуры по `condition_key` (канонический key).

    Args:
        services: Сервисы и структуры.
        condition_key: Канонический ключ условия (например, `blue`). Пустое значение → вернуть всё.

    Returns:
        Новый словарь сервисов, где оставлены только структуры с подходящим `condition`.
    """
    key = (condition_key or "").strip().lower()
    if not key:
        return dict(services)

    filtered: dict[str, list[StructureInfo]] = {}
    for service_key, structures in services.items():
        filtered_structures = [s for s in structures if s.condition and s.condition.strip().lower() == key]
        if filtered_structures:
            filtered[service_key] = filtered_structures

    return filtered
