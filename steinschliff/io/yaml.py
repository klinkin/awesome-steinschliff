"""
Функции чтения YAML и связанных метаданных.

Почему отдельный модуль:
    `steinschliff.utils` исторически разросся и смешал UI/логирование и I/O.
    Этот модуль — чистый "I/O слой": чтение файлов + (частичная) валидация входа.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from steinschliff.models import SchliffStructure, ServiceMetadata
from steinschliff.ui.rich import print_items_panel, print_kv_panel, print_validation_errors

logger = logging.getLogger("steinschliff.io.yaml")


def _validate_meta_file(data: dict[str, Any], path: Path) -> ServiceMetadata | dict[str, Any]:
    """Валидировать `_meta.yaml` и вернуть `ServiceMetadata`.

    Args:
        data: Сырые данные YAML (mapping).
        path: Путь к файлу (для сообщений об ошибках).

    Returns:
        `ServiceMetadata` при успехе или исходный `dict` при ошибке валидации.
    """
    try:
        return ServiceMetadata.model_validate(data)
    except ValidationError as e:
        if logger.isEnabledFor(logging.WARNING):
            print_validation_errors(e, str(path))
        return data


def _validate_structure_file(data: dict[str, Any], path: Path) -> dict[str, Any] | None:
    """Валидировать YAML-файл структуры.

    Args:
        data: Сырые данные YAML (mapping).
        path: Путь к файлу (для сообщений об ошибках).

    Returns:
        - dict валидированных данных (normal case)
        - dict исходных данных с `_partial_validation=True`, если можно “частично принять”
        - `None`, если файл непригоден для использования
    """
    try:
        return SchliffStructure.model_validate(data).model_dump(exclude_unset=True)
    except ValidationError as e:
        if logger.isEnabledFor(logging.WARNING):
            print_validation_errors(e, str(path))

        if "name" in data and "description" in data:
            # Табличное уведомление о частичной валидации
            print_kv_panel(
                title="Частичная валидация",
                rows=[("Файл", str(path))],
                border_style="yellow",
            )
            # Помечаем как частично валидированный, чтобы отразить это в сводке
            data["_partial_validation"] = True
            return data

        logger.error("Файл %s не содержит обязательных полей и не может быть использован", path)
        return None


def _load_yaml_data(path: Path) -> dict[str, Any] | None:
    """Прочитать YAML-файл и убедиться, что на верхнем уровне находится mapping.

    Args:
        path: Путь к YAML-файлу.

    Returns:
        Словарь (mapping) или `None`, если файл не найден/битый/не имеет корректной структуры.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

            if data is None:
                data = {}

            if not isinstance(data, dict):
                logger.error(
                    "Файл %s должен содержать YAML-объект (mapping), получен %s",
                    path,
                    type(data).__name__,
                )
                return None

            return data

    except yaml.YAMLError as e:
        logger.error("Ошибка разбора YAML в %s: %s", path, e)
        return None
    except FileNotFoundError:
        logger.error("Файл не найден: %s", path)
        return None
    except PermissionError:
        logger.error("Отказано в доступе: %s", path)
        return None
    except (OSError, UnicodeDecodeError) as e:
        logger.error("Ошибка чтения файла %s: %s", path, e)
        return None


def read_yaml_file(file_path: str | Path) -> dict[str, Any] | ServiceMetadata | None:
    """Прочитать YAML-файл и (частично) провалидировать через Pydantic.

    Поведение зависит от файла:
    - `_meta.yaml`: возвращает `ServiceMetadata` (или `dict`, если мета-файл невалиден)
    - файл структуры: возвращает `dict` валидированных данных или `dict` с `_partial_validation=True`
    - при ошибках чтения/структуры: возвращает `None`

    Args:
        file_path: Путь к YAML-файлу.

    Returns:
        Объект данных (`ServiceMetadata`/`dict`) или `None`, если файл непригоден.
    """
    path = Path(file_path) if not isinstance(file_path, Path) else file_path

    data = _load_yaml_data(path)
    if data is None:
        return None

    if path.name == "_meta.yaml":
        return _validate_meta_file(data, path)
    return _validate_structure_file(data, path)


def find_yaml_files(directory: str) -> list[str]:
    """Найти все `.yaml` файлы в директории рекурсивно.

    Args:
        directory: Директория для поиска.

    Returns:
        Список путей к YAML-файлам.
    """
    dir_path = Path(directory)
    yaml_files = list(dir_path.glob("**/*.yaml"))
    return [str(path) for path in yaml_files]


def _process_service_metadata(
    service: str,
    metadata_file: Path,
    metadata: dict[str, ServiceMetadata],
    metadata_warnings: list[str],
    metadata_errors: list[tuple[str, str]],
) -> None:
    """Обработать метаданные одного сервиса и обновить агрегаты.

    Args:
        service: Ключ сервиса (имя папки).
        metadata_file: Путь к `_meta.yaml`.
        metadata: Агрегируемый результат `service -> ServiceMetadata`.
        metadata_warnings: Список сервисов с пустыми/непрочитанными метаданными.
        metadata_errors: Список ошибок чтения метаданных.
    """
    try:
        service_meta = read_yaml_file(metadata_file)
        if service_meta:
            if isinstance(service_meta, dict):
                try:
                    service_meta = ServiceMetadata.model_validate(service_meta)
                except ValidationError:
                    service_meta = ServiceMetadata(name=service)

            metadata[service] = service_meta
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Прочитаны метаданные для сервиса %s", service)
        else:
            metadata[service] = ServiceMetadata(name=service)
            metadata_warnings.append(service)
    except (OSError, yaml.YAMLError, ValidationError) as e:
        metadata_errors.append((service, str(e)))
        metadata[service] = ServiceMetadata(name=service)


def _log_metadata_results(
    metadata_warnings: list[str],
    metadata_errors: list[tuple[str, str]],
    metadata: dict[str, ServiceMetadata],
) -> None:
    """Показать сводку по метаданным сервисов (через Rich UI).

    Args:
        metadata_warnings: Сервисы с предупреждениями.
        metadata_errors: Сервисы с ошибками.
        metadata: Итоговый словарь метаданных (для вывода общего количества).
    """
    if metadata_warnings:
        items = [f"[yellow]{service}[/]" for service in metadata_warnings]
        print_items_panel("Пустые файлы метаданных для сервисов", items, border_style="yellow")

    if metadata_errors:
        # Переиспользуем print_kv_panel, чтобы не плодить ещё одну таблицу.
        # При желании можно вернуть Rich-таблицу, но это уже UI слой.
        print_kv_panel(
            "Ошибки чтения метаданных",
            [(service, error) for service, error in metadata_errors],
            border_style="red",
        )

    print_kv_panel("Итоги метаданных сервисов", [("Всего", str(len(metadata)))], border_style="blue")


def read_service_metadata(metadata_dir: str, services: list[str]) -> dict[str, ServiceMetadata]:
    """Прочитать метаданные сервисов из файлов `_meta.yaml`.

    Args:
        metadata_dir: Корневая директория, где лежат папки сервисов.
        services: Список ключей сервисов (имена папок).

    Returns:
        Словарь `service_key -> ServiceMetadata` для тех сервисов, у которых существует `_meta.yaml`.
    """
    metadata: dict[str, ServiceMetadata] = {}
    metadata_warnings: list[str] = []
    metadata_errors: list[tuple[str, str]] = []

    metadata_path = Path(metadata_dir)
    if not metadata_path.exists() or not metadata_path.is_dir():
        logger.warning("Директория с метаданными не найдена: %s", metadata_dir)
        return metadata

    for service in services:
        metadata_file = metadata_path / service / "_meta.yaml"
        if metadata_file.exists():
            _process_service_metadata(service, metadata_file, metadata, metadata_warnings, metadata_errors)

    _log_metadata_results(metadata_warnings, metadata_errors, metadata)
    return metadata
