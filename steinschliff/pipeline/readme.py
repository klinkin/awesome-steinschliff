"""Шаги pipeline для генерации README.

Модуль выделен для упрощения тестирования генерации по шагам:
load → validate → transform → render.

Здесь нет вывода в консоль и прогресс-баров — только “чистые” функции, которые
принимают данные и возвращают результаты.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from steinschliff.formatters import format_snow_types
from steinschliff.io import find_yaml_files, read_yaml_file
from steinschliff.models import Service, ServiceMetadata, StructureInfo


@dataclass(frozen=True)
class LoadValidationStats:
    """Статистика чтения/валидации YAML-файлов.

    Attributes:
        valid_files: Количество полностью валидных файлов структур.
        warning_files: Количество файлов, прошедших частичную валидацию.
        error_files: Количество файлов, которые не удалось прочитать/использовать.
        processed_structures: Количество структур, успешно загруженных в результат.
    """

    valid_files: int
    warning_files: int
    error_files: int
    processed_structures: int


@dataclass(frozen=True)
class LoadedStructures:
    """Результат шага load+validate для структур.

    Attributes:
        services: Маппинг `service_key -> list[StructureInfo]`.
        name_to_path: Маппинг `structure_name -> file_path`.
        stats: Статистика валидации/ошибок.
    """

    services: dict[str, list[StructureInfo]]
    name_to_path: dict[str, str]
    stats: LoadValidationStats


def discover_yaml_files(*, schliffs_dir: Path) -> list[Path]:
    """LOAD: найти все YAML-файлы в `schliffs_dir` (включая `_meta.yaml`).

    Args:
        schliffs_dir: Корневая директория каталога `schliffs/`.

    Returns:
        Список путей к YAML-файлам.
    """
    return [Path(p) for p in find_yaml_files(str(schliffs_dir))]


def load_structures_from_yaml_files(*, yaml_files: list[Path], schliffs_dir: Path) -> LoadedStructures:
    """LOAD+VALIDATE: прочитать YAML-файлы структур и собрать `services/name_to_path`.

    Файлы `_meta.yaml` пропускаются.

    Особенность:
        Если файл невалиден, но содержит `name` и `description`, то `read_yaml_file`
        может вернуть частично валидированный dict с флагом `_partial_validation=True`.
        Такие файлы считаются “warning”, но структура всё равно попадает в выдачу.

    Args:
        yaml_files: Список YAML-файлов (может включать `_meta.yaml`).
        schliffs_dir: Корневая директория каталога `schliffs/` (нужна для вычисления `service_key`).

    Returns:
        `LoadedStructures` с сервисами, индексом по имени и статистикой.
    """
    services: dict[str, list[StructureInfo]] = {}
    name_to_path: dict[str, str] = {}

    valid_files = 0
    warning_files = 0
    error_files = 0
    processed_structures = 0

    schliffs_prefix = f"{str(schliffs_dir).rstrip('/')}/"

    for file_path in yaml_files:
        if file_path.name == "_meta.yaml":
            continue

        data = read_yaml_file(file_path)
        if not data:
            error_files += 1
            continue

        # read_yaml_file для структур возвращает dict (или dict с _partial_validation).
        if not isinstance(data, dict):
            error_files += 1
            continue

        is_partial_validation = bool(data.get("_partial_validation"))
        if is_partial_validation:
            warning_files += 1
        else:
            valid_files += 1

        name = data.get("name", file_path.stem)
        name_str = str(name)
        name_to_path[name_str] = str(file_path)

        service_key = str(file_path.parent)
        if service_key.startswith(schliffs_prefix):
            service_key = service_key[len(schliffs_prefix) :]
        if not service_key:
            service_key = "main"

        formatted_snow_type = format_snow_types(data.get("snow_type", []))

        service_data = data.get("service", {})
        if isinstance(service_data, dict):
            service_obj = Service(name=str(service_data.get("name", "")))
        else:
            service_obj = Service(name=str(service_data or ""))

        structure_info = StructureInfo(
            name=name_str,
            description=data.get("description", ""),
            description_ru=data.get("description_ru", ""),
            snow_type=formatted_snow_type,
            temperature=data.get("temperature", []),
            condition=data.get("condition", ""),
            service=service_obj,
            country=data.get("country", ""),
            tags=data.get("tags", []),
            similars=data.get("similars", []),
            features=data.get("features", []),
            images=data.get("images", []),
            file_path=str(file_path),
        )

        services.setdefault(service_key, []).append(structure_info)
        processed_structures += 1

    return LoadedStructures(
        services=services,
        name_to_path=name_to_path,
        stats=LoadValidationStats(
            valid_files=valid_files,
            warning_files=warning_files,
            error_files=error_files,
            processed_structures=processed_structures,
        ),
    )


def prepare_countries_data(
    *,
    services: dict[str, list[StructureInfo]],
    service_metadata: dict[str, ServiceMetadata],
) -> dict[str, Any]:
    """TRANSFORM: сгруппировать сервисы по странам и подготовить данные для шаблона.

    Args:
        services: Маппинг `service_key -> list[StructureInfo]`.
        service_metadata: Маппинг `service_key -> ServiceMetadata`.

    Returns:
        Словарь с ключами:
        - `countries`: иерархия `country -> services -> service_key -> data`
        - `ordered_countries`: список стран в порядке вывода (Россия → остальные → Other).
    """
    countries: dict[str, dict[str, Any]] = {}

    for service_name, structures in services.items():
        country = "Other"
        if service_name in service_metadata:
            service_meta = service_metadata[service_name]
            if service_meta.country:
                country = service_meta.country

        service_meta_opt: ServiceMetadata | None = service_metadata.get(service_name)

        if country not in countries:
            countries[country] = {"services": {}}

        service_data: dict[str, Any] = {"name": service_name, "structures": structures}

        if service_meta_opt:
            service_data.update(
                {
                    "title": service_meta_opt.name or service_name.capitalize(),
                    "city": service_meta_opt.city or "",
                    "description": service_meta_opt.description or "",
                    "description_ru": service_meta_opt.description_ru or "",
                    "website_url": service_meta_opt.website_url or "",
                    "video_url": service_meta_opt.video_url or "",
                    "contact": service_meta_opt.contact or {},
                }
            )
        else:
            service_data.update(
                {
                    "title": service_name.capitalize(),
                    "city": "",
                    "description": "",
                    "description_ru": "",
                    "website_url": "",
                    "video_url": "",
                    "contact": {},
                }
            )

        countries[country]["services"][service_name] = service_data

    ordered_countries: list[str] = []
    if "Россия" in countries:
        ordered_countries.append("Россия")
    for country in sorted(countries.keys()):
        if country != "Россия" and country != "Other":
            ordered_countries.append(country)
    if "Other" in countries and countries["Other"]["services"]:
        ordered_countries.append("Other")

    return {"countries": countries, "ordered_countries": ordered_countries}


def get_structure_sort_key(*, sort_field: str, structure: StructureInfo) -> Any:
    """TRANSFORM: вычислить ключ сортировки структуры.

    Args:
        sort_field: Поле сортировки (например, `temperature` или `name`).
        structure: Структура.

    Returns:
        Ключ сортировки. Для `temperature` возвращает значение, позволяющее
        сортировать “сначала тёплые”, а структуры без температуры отправлять в конец.
    """
    if sort_field == "temperature":
        if structure.temperature and isinstance(structure.temperature, list) and structure.temperature[0]:
            temp_range = structure.temperature[0]
            max_temp = temp_range.get("max")
            if max_temp is not None:
                try:
                    return -float(max_temp)
                except (ValueError, TypeError):
                    pass
        return float("inf")
    return getattr(structure, sort_field, "") or ""


def sort_countries_data_in_place(*, countries_data: dict[str, Any], sort_field: str) -> None:
    """TRANSFORM: отсортировать структуры внутри каждого сервиса (in-place).

    Сейчас сортировка применяется только для `sort_field="temperature"`.

    Args:
        countries_data: Данные, возвращаемые `prepare_countries_data`.
        sort_field: Поле сортировки.
    """
    if sort_field != "temperature":
        return

    for country in countries_data["countries"].values():
        for _service_name, service_data in country["services"].items():
            structures = service_data["structures"]
            service_data["structures"] = sorted(
                structures,
                key=lambda s: get_structure_sort_key(sort_field=sort_field, structure=s),
            )


def build_template_data(
    *,
    countries_data: dict[str, Any],
    sort_field: str,
    output_dir: Path,
    language: str,
    description_field: str,
) -> dict[str, Any]:
    """RENDER: собрать словарь данных для передачи в Jinja2-шаблон.

    Args:
        countries_data: Данные, возвращаемые `prepare_countries_data`.
        sort_field: Поле сортировки (передаётся в шаблон).
        output_dir: Директория вывода (нужна для относительных ссылок).
        language: Язык рендера (`ru`/`en`).
        description_field: Поле описания в структуре (`description`/`description_ru`).

    Returns:
        Словарь с данными, ожидаемыми шаблоном `readme.jinja2`.
    """
    return {
        "countries": countries_data["countries"],
        "ordered_countries": countries_data["ordered_countries"],
        "sort_by": sort_field,
        "output_dir": str(output_dir),
        "language": language,
        "description_field": description_field,
    }
