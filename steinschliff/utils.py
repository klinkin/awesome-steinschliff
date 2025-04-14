"""
Вспомогательные функции для Steinschliff.
"""

import glob
import logging
import os
from typing import Any, Dict, List, Optional

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

    report = [
        f"{BOLD}===== РЕЗУЛЬТАТЫ ВАЛИДАЦИИ YAML-ФАЙЛОВ ====={RESET}",
        f"{GREEN}✓ Успешно:{RESET}       {valid_files} из {total} ({valid_files/total*100:.1f}%)",
        f"{YELLOW}⚠ Предупреждения:{RESET} {warning_files} из {total} ({warning_files/total*100:.1f}%)",
        f"{RED}✗ Ошибки:{RESET}         {error_files} из {total} ({error_files/total*100:.1f}%)",
    ]

    logger.info("\n" + "\n".join(report))


def read_yaml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Читает и разбирает YAML-файл с помощью PyYAML и валидирует с помощью Pydantic.

    Args:
        file_path: Путь к YAML-файлу.

    Returns:
        Словарь с разобранным содержимым YAML или None, если произошла ошибка.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

            # Пропускаем валидацию для метафайлов или используем специальную модель
            filename = os.path.basename(file_path)
            if filename == "_meta.yaml":
                try:
                    # Валидируем метаданные сервиса
                    validated_data = ServiceMetadata.model_validate(data).model_dump(exclude_unset=True)
                    return validated_data
                except ValidationError as e:
                    # Подробный вывод ошибок валидации
                    error_report = format_validation_error(e, file_path)
                    logger.warning(f"\n{error_report}")
                    return data  # Возвращаем оригинальные данные, если валидация не прошла

            # Валидация структуры с помощью Pydantic
            try:
                validated_data = SchliffStructure.model_validate(data).model_dump(exclude_unset=True)
                return validated_data
            except ValidationError as e:
                # Подробный вывод ошибок валидации
                error_report = format_validation_error(e, file_path)
                logger.warning(f"\n{error_report}")

                # Если есть минимальные обязательные поля, используем исходные данные
                if "name" in data and "description" in data:
                    logger.info(f"Файл {file_path} содержит обязательные поля, используем с неполной валидацией")
                    return data

                logger.error(f"Файл {file_path} не содержит обязательных полей и не может быть использован")
                return None

    except yaml.YAMLError as e:
        logger.error(f"Ошибка разбора YAML в {file_path}: {e}")
        return None
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return None
    except PermissionError:
        logger.error(f"Отказано в доступе: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {e}")
        return None


def find_yaml_files(directory: str) -> List[str]:
    """
    Находит все YAML-файлы в указанной директории и её поддиректориях.

    Args:
        directory: Корневая директория для поиска.

    Returns:
        Список путей к файлам.
    """
    pattern = os.path.join(directory, "**", "*.yaml")
    return glob.glob(pattern, recursive=True)


def read_service_metadata(metadata_dir: str, services: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Читает метаданные сервисов из файлов _meta.yaml.

    Args:
        metadata_dir: Корневая директория с сервисами (обычно schliffs).
        services: Список сервисов.

    Returns:
        Словарь метаданных сервисов.
    """
    metadata = {}

    # Проверяем существование директории
    if not os.path.exists(metadata_dir) or not os.path.isdir(metadata_dir):
        logger.warning(f"Директория с метаданными не найдена: {metadata_dir}")
        return metadata

    # Для каждого сервиса проверяем наличие файла метаданных
    for service in services:
        # Ищем _meta.yaml внутри директории сервиса
        metadata_file = os.path.join(metadata_dir, service, "_meta.yaml")

        if os.path.exists(metadata_file):
            try:
                service_meta = read_yaml_file(metadata_file)
                if service_meta:
                    metadata[service] = service_meta
                    logger.debug(f"Прочитаны метаданные для сервиса {service}")
                else:
                    logger.warning(f"Пустой файл метаданных для сервиса {service}")
            except Exception as e:
                logger.error(f"Ошибка чтения метаданных для сервиса {service}: {e}")

    logger.info(f"Найдено {len(metadata)} файлов метаданных сервисов")
    return metadata


def setup_logging(level: int = logging.INFO) -> None:
    """
    Настраивает логирование для приложения.

    Args:
        level: Уровень логирования.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info(f"Логирование настроено с уровнем {logging.getLevelName(level)}")
