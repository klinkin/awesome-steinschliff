"""
Вспомогательные функции для Steinschliff.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

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


def print_validation_summary(valid_files: int, error_files: int, warning_files: int) -> None:
    """
    Выводит сводку по результатам валидации YAML-файлов.

    Args:
        valid_files: Количество валидных файлов
        error_files: Количество файлов с ошибками
        warning_files: Количество файлов с предупреждениями
    """
    total = valid_files + error_files + warning_files

    # Проверяем, включен ли уровень INFO
    if not logger.isEnabledFor(logging.INFO):
        return

    valid_percent = valid_files / total * 100 if total > 0 else 0
    warning_percent = warning_files / total * 100 if total > 0 else 0
    error_percent = error_files / total * 100 if total > 0 else 0

    report = [
        f"{BOLD}===== РЕЗУЛЬТАТЫ ВАЛИДАЦИИ YAML-ФАЙЛОВ ====={RESET}",
        f"{GREEN}✓ Успешно:{RESET}       {valid_files} из {total} ({valid_percent:.1f}%)",
        f"{YELLOW}⚠ Предупреждения:{RESET} {warning_files} из {total} ({warning_percent:.1f}%)",
        f"{RED}✗ Ошибки:{RESET}         {error_files} из {total} ({error_percent:.1f}%)",
    ]

    # Используем параметризованное логирование вместо конкатенации
    report_str = "\n".join(report)
    logger.info("\n%s", report_str)


def read_yaml_file(file_path: Union[str, Path]) -> Union[Dict[str, Any], ServiceMetadata, None]:
    """
    Читает и разбирает YAML-файл с помощью PyYAML и валидирует с помощью Pydantic.

    Args:
        file_path: Путь к YAML-файлу (строка или Path).

    Returns:
        Для _meta.yaml - объект ServiceMetadata,
        для других файлов - словарь с разобранным содержимым YAML,
        или None, если произошла ошибка.
    """
    # Преобразуем строку в Path, если нужно
    path = Path(file_path) if not isinstance(file_path, Path) else file_path

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

            # Пропускаем валидацию для метафайлов или используем специальную модель
            if path.name == "_meta.yaml":
                try:
                    # Валидируем метаданные сервиса и возвращаем объект модели
                    return ServiceMetadata.model_validate(data)
                except ValidationError as e:
                    # Подробный вывод ошибок валидации только если включен WARNING
                    if logger.isEnabledFor(logging.WARNING):
                        error_report = format_validation_error(e, str(path))
                        logger.warning("\n%s", error_report)
                    return data  # Возвращаем оригинальные данные, если валидация не прошла

            # Валидация структуры с помощью Pydantic
            try:
                validated_data = SchliffStructure.model_validate(data).model_dump(exclude_unset=True)
                return validated_data
            except ValidationError as e:
                # Подробный вывод ошибок валидации только если включен WARNING
                if logger.isEnabledFor(logging.WARNING):
                    error_report = format_validation_error(e, str(path))
                    logger.warning("\n%s", error_report)

                # Если есть минимальные обязательные поля, используем исходные данные
                if "name" in data and "description" in data:
                    logger.info("Файл %s содержит обязательные поля, используем с неполной валидацией", path)
                    return data

                logger.error("Файл %s не содержит обязательных полей и не может быть использован", path)
                return None

    except yaml.YAMLError as e:
        logger.error("Ошибка разбора YAML в %s: %s", path, e)
        return None
    except FileNotFoundError:
        logger.error("Файл не найден: %s", path)
        return None
    except PermissionError:
        logger.error("Отказано в доступе: %s", path)
        return None
    except Exception as e:
        logger.error("Ошибка чтения файла %s: %s", path, e)
        return None


def find_yaml_files(directory: str) -> List[str]:
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


def read_service_metadata(metadata_dir: str, services: List[str]) -> Dict[str, ServiceMetadata]:
    """
    Читает метаданные сервисов из файлов _meta.yaml.

    Args:
        metadata_dir: Корневая директория с сервисами (обычно schliffs).
        services: Список сервисов.

    Returns:
        Словарь объектов ServiceMetadata, проиндексированных по имени сервиса.
    """
    metadata = {}
    metadata_warnings = []
    metadata_errors = []

    # Создаем Path-объект для директории метаданных
    metadata_path = Path(metadata_dir)

    # Проверяем существование директории
    if not metadata_path.exists() or not metadata_path.is_dir():
        logger.warning("Директория с метаданными не найдена: %s", metadata_dir)
        return metadata

    # Для каждого сервиса проверяем наличие файла метаданных
    for service in services:
        # Ищем _meta.yaml внутри директории сервиса
        metadata_file = metadata_path / service / "_meta.yaml"

        if metadata_file.exists():
            try:
                service_meta = read_yaml_file(metadata_file)
                if service_meta:
                    # Если вернулся словарь (из-за ошибки валидации), преобразуем его в ServiceMetadata
                    if isinstance(service_meta, dict):
                        try:
                            service_meta = ServiceMetadata.model_validate(service_meta)
                        except ValidationError:
                            # Если и это не удалось, создаем пустой объект
                            service_meta = ServiceMetadata(name=service)

                    metadata[service] = service_meta
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Прочитаны метаданные для сервиса %s", service)
                else:
                    # Создаем пустой объект метаданных
                    metadata[service] = ServiceMetadata(name=service)
                    metadata_warnings.append(service)
            except Exception as e:
                metadata_errors.append((service, str(e)))
                # Создаем пустой объект метаданных при ошибке
                metadata[service] = ServiceMetadata(name=service)

    # Логируем предупреждения и ошибки один раз после всей обработки
    if metadata_warnings and logger.isEnabledFor(logging.WARNING):
        logger.warning("Пустые файлы метаданных для сервисов: %s", ", ".join(metadata_warnings))

    if metadata_errors and logger.isEnabledFor(logging.ERROR):
        for service, error in metadata_errors:
            logger.error("Ошибка чтения метаданных для сервиса %s: %s", service, error)

    logger.info("Найдено %d файлов метаданных сервисов", len(metadata))
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

    # Создаем консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Создаем форматтер для более информативного вывода
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)

    # Добавляем обработчик к корневому логгеру
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Настраиваем наш основной логгер
    logger.setLevel(level)

    # Используем параметризованное логирование вместо f-строк
    logger.info("Логирование настроено с уровнем %s", logging.getLevelName(level))
