"""
Вспомогательные функции для Steinschliff.
"""

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as rich_traceback_install

from steinschliff.models import SchliffStructure, ServiceMetadata

# Константы для цветного вывода в терминал
RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
BOLD = "\033[1m"

logger = logging.getLogger("steinschliff.utils")
console = Console()


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


def print_kv_panel(title: str, rows: list[tuple[str, str]], border_style: str = "cyan") -> None:
    """
    Выводит ключ-значение в виде компактной таблицы в панели.

    Args:
        title: Заголовок панели
        rows: Список пар (ключ, значение)
        border_style: Цвет рамки панели
    """
    table = Table.grid(padding=(0, 1))
    for key, value in rows:
        table.add_row(f"[bold]{key}[/]:", f"[cyan]{value}[/]")
    console.print(Panel.fit(table, title=title, border_style=border_style))


def print_items_panel(title: str, items: list[str], border_style: str = "yellow") -> None:
    """
    Выводит список строк в виде таблицы в панели.

    Args:
        title: Заголовок панели
        items: Список строк
        border_style: Цвет рамки панели
    """
    table = Table(show_header=False, box=None)
    table.add_column("Элемент")
    for item in items:
        table.add_row(item)
    console.print(Panel.fit(table, title=title, border_style=border_style))


def print_validation_errors(err: ValidationError, file_path: str) -> None:
    """
    Печатает ошибки валидации в виде таблицы Rich.

    Args:
        err: Объект ошибки ValidationError
        file_path: Путь к файлу с ошибкой
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
    """
    Выводит сводку по результатам валидации YAML-файлов с использованием Rich.

    Args:
        valid_files: Количество валидных файлов
        error_files: Количество файлов с ошибками
        warning_files: Количество файлов с предупреждениями
    """
    # Проверяем, включен ли уровень INFO
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


def _validate_meta_file(data: dict[str, Any], path: Path) -> ServiceMetadata | dict[str, Any]:
    """
    Валидирует метафайл и возвращает объект ServiceMetadata или исходные данные.

    Args:
        data: Данные из YAML файла
        path: Путь к файлу

    Returns:
        ServiceMetadata объект или исходные данные
    """
    try:
        return ServiceMetadata.model_validate(data)
    except ValidationError as e:
        if logger.isEnabledFor(logging.WARNING):
            print_validation_errors(e, str(path))
        return data


def _validate_structure_file(data: dict[str, Any], path: Path) -> dict[str, Any] | None:
    """
    Валидирует файл структуры и возвращает валидированные данные или None.

    Args:
        data: Данные из YAML файла
        path: Путь к файлу

    Returns:
        Валидированные данные или None
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
            if isinstance(data, dict):
                data["_partial_validation"] = True
            return data

        logger.error("Файл %s не содержит обязательных полей и не может быть использован", path)
        return None


def _load_yaml_data(path: Path) -> dict[str, Any] | None:
    """
    Загружает и проверяет базовую структуру YAML файла.

    Args:
        path: Путь к файлу

    Returns:
        Данные из файла или None при ошибке
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
    """
    Читает и разбирает YAML-файл с помощью PyYAML и валидирует с помощью Pydantic.

    Args:
        file_path: Путь к YAML-файлу (строка или Path).

    Returns:
        Для `_meta.yaml` – объект :class:`ServiceMetadata` при успешной валидации,
        либо исходный словарь при ошибках валидации.
        Для других файлов – словарь с разобранным содержимым YAML при успешной
        валидации, либо исходные данные при наличии обязательных полей.
        Возвращает ``None``, если файл пуст, не содержит требуемых полей или
        произошла ошибка.
    """
    path = Path(file_path) if not isinstance(file_path, Path) else file_path

    data = _load_yaml_data(path)
    if data is None:
        return None

    if path.name == "_meta.yaml":
        return _validate_meta_file(data, path)
    return _validate_structure_file(data, path)


def find_yaml_files(directory: str) -> list[str]:
    """
    Находит все YAML-файлы в указанной директории и её поддиректориях.

    Args:
        directory: Корневая директория для поиска.

    Returns:
        Список путей к файлам.
    """
    # Создаем объект Path из директории
    dir_path = Path(directory)

    # Используем метод .glob() объекта Path для рекурсивного поиска
    yaml_files = list(dir_path.glob("**/*.yaml"))

    # Преобразуем объекты Path в строковые пути для совместимости
    return [str(path) for path in yaml_files]


def _process_service_metadata(
    service: str,
    metadata_file: Path,
    metadata: dict[str, ServiceMetadata],
    metadata_warnings: list[str],
    metadata_errors: list[tuple[str, str]],
) -> None:
    """
    Обрабатывает метаданные для одного сервиса.

    Args:
        service: Имя сервиса
        metadata_file: Путь к файлу метаданных
        metadata: Словарь для хранения метаданных
        metadata_warnings: Список предупреждений
        metadata_errors: Список ошибок
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
    metadata_warnings: list[str], metadata_errors: list[tuple[str, str]], metadata: dict[str, ServiceMetadata]
) -> None:
    """
    Логирует результаты обработки метаданных.

    Args:
        metadata_warnings: Список предупреждений
        metadata_errors: Список ошибок
        metadata: Словарь метаданных
    """
    # Таблица предупреждений по метаданным
    if metadata_warnings:
        items = [f"[yellow]{service}[/]" for service in metadata_warnings]
        print_items_panel("Пустые файлы метаданных для сервисов", items, border_style="yellow")

    # Таблица ошибок по метаданным
    if metadata_errors:
        table = Table(show_header=True, header_style="bold red", box=None)
        table.add_column("Сервис")
        table.add_column("Ошибка")
        for service, error in metadata_errors:
            table.add_row(f"[bold]{service}[/]", f"[red]{error}[/]")
        console.print(Panel.fit(table, title="Ошибки чтения метаданных", border_style="red"))

    # Сводка по метаданным
    print_kv_panel("Итоги метаданных сервисов", [("Всего", str(len(metadata)))], border_style="blue")


def read_service_metadata(metadata_dir: str, services: list[str]) -> dict[str, ServiceMetadata]:
    """
    Читает метаданные сервисов из файлов _meta.yaml.

    Args:
        metadata_dir: Корневая директория с сервисами (обычно schliffs).
        services: Список сервисов.

    Returns:
        Словарь объектов ServiceMetadata, проиндексированных по имени сервиса.
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


def setup_logging(level: int = logging.INFO) -> None:
    """
    Настраивает логирование для приложения с использованием лучших практик.
    Настраивает только консольное логирование, без ротации.

    Args:
        level: Уровень логирования.
    """
    # Удаляем все существующие обработчики, чтобы избежать дублирования
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    rich_traceback_install(show_locals=True)
    console_handler: logging.Handler = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
    console_handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)

    # Добавляем обработчик к корневому логгеру
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Настраиваем наш основной логгер
    logger.setLevel(level)

    # Используем параметризованное логирование вместо f-строк
    logger.info("Логирование настроено с уровнем %s", logging.getLevelName(level))
