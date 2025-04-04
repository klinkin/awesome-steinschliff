"""
Генератор README для Steinschliff

Этот скрипт генерирует файлы README.md и README_en.md с структурированной
информацией о структурах для беговых лыж из конфигурационных файлов YAML.

Пример YAML файла структуры:
```yaml
name: С1-1
description: Fine linear structure for cold conditions
description_ru: Тонкая линейная структура для холодных условий
snow_type:
  - New
  - Fine grained
snow_temperature:
  - min: -25
    max: -10
house: Uventa
country: Russia
tags:
  - cold
  - race
similars:
  - C2-1
  - F1
```

Использование:
    ./gen_readme.py [--debug] [--config CONFIG] [--en-header FILE] [--ru-header FILE]
                    [--sort-by FIELD] [--filter PATTERN]
"""

import os
import glob
import logging
import argparse
import re
import json
from collections import defaultdict
from typing import Dict, List, Any, Optional, Union

# Константы для цветного вывода в терминал
RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
BOLD = "\033[1m"

# Импорт библиотеки PyYAML и Pydantic
try:
    import yaml
    from pydantic import BaseModel, Field, ValidationError
except ImportError:
    missing_lib = "pydantic" if "pydantic" not in locals() else "pyyaml"
    print(f"Требуется библиотека {missing_lib}. Установите её с помощью pip: pip install {missing_lib}")
    exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("readme_generator")

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    "schliffs_dir": "schliffs",
    "readme_file": "README_en.md",
    "readme_ru_file": "README.md",
    "header_templates": {
        "en": "scripts/templates/readme_en_header.md",
        "ru": "scripts/templates/readme_ru_header.md"
    },
    "sort_field": "name",
    "filter_pattern": None,
    "exclude_empty_sections": False
}

# Определение Pydantic-моделей для валидации
class TemperatureRange(BaseModel):
    """Диапазон температуры снега"""
    min: float
    max: float

class SchliffStructure(BaseModel):
    """Модель структуры"""
    name: str
    description: str
    description_ru: Optional[str] = ""
    snow_type: Union[List[str], str] = []
    snow_temperature: Optional[List[TemperatureRange]] = []
    house: Optional[str] = ""
    country: Optional[str] = ""
    tags: Optional[List[str]] = []
    similars: Optional[List[str]] = []

    class Config:
        """Конфигурация модели Pydantic"""
        extra = "allow"  # Разрешаем дополнительные поля

class SectionMetadata(BaseModel):
    """Модель метаданных секции (производителя)"""
    name: Optional[str] = ""
    description: Optional[str] = ""
    description_ru: Optional[str] = ""
    website_url: Optional[str] = ""
    video_url: Optional[str] = ""

    class Config:
        """Конфигурация модели Pydantic"""
        extra = "allow"  # Разрешаем дополнительные поля


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Загружает конфигурацию из YAML-файла.

    Args:
        config_file: Путь к файлу конфигурации.

    Returns:
        Словарь с настройками конфигурации.
    """
    config = DEFAULT_CONFIG.copy()

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config and isinstance(user_config, dict):
                    # Обновляем только существующие ключи, чтобы предотвратить неожиданные настройки
                    for key in config.keys():
                        if key in user_config:
                            config[key] = user_config[key]
            logger.info(f"Загружена конфигурация из {config_file}")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации из {config_file}: {e}")

    return config


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
        f"{RED}✗ Ошибки:{RESET}         {error_files} из {total} ({error_files/total*100:.1f}%)"
    ]

    logger.info("\n" + "\n".join(report))


def read_yaml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Читает и разбирает YAML-файл с помощью PyYAML и валидирует с помощью Pydantic.

    Args:
        file_path: Путь к YAML-файлу.

    Returns:
        Словарь с разобранным содержимым YAML или None, если произошла ошибка.

    Raises:
        Exception: Если файл не может быть прочитан или разобран.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

            # Пропускаем валидацию для метафайлов или используем специальную модель
            filename = os.path.basename(file_path)
            if filename == "_meta.yaml":
                try:
                    # Валидируем метаданные секции
                    validated_data = SectionMetadata.model_validate(data).model_dump(exclude_unset=True)
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


def read_header_file(file_path: str) -> str:
    """
    Читает содержимое из файла-шаблона заголовка.

    Args:
        file_path: Путь к файлу-шаблону заголовка.

    Returns:
        Строка с содержимым заголовка или пустая строка, если файл не найден.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Файл заголовка {file_path} не найден, используется пустой заголовок")
        return ""
    except Exception as e:
        logger.error(f"Ошибка чтения файла заголовка {file_path}: {e}")
        return ""


def format_snow_types(snow_types: Union[List[str], str, None]) -> str:
    """
    Форматирует список типов снега для отображения в таблицах README.

    Args:
        snow_types: Список типов снега или строка.

    Returns:
        Отформатированная строка с типами снега, разделенными запятыми.
    """
    if not snow_types:
        return ""

    if isinstance(snow_types, list):
        # Фильтруем значения None и конвертируем в строки
        valid_types = [str(item) for item in snow_types if item is not None]
        return ", ".join(valid_types)

    return str(snow_types)


def format_list_for_display(items: Union[List[str], str, None]) -> str:
    """
    Форматирует список элементов для отображения в таблицах README.

    Args:
        items: Список элементов или строка.

    Returns:
        Отформатированная строка с элементами, разделенными запятыми.
    """
    if not items:
        return ""

    if isinstance(items, list):
        # Фильтруем значения None и пустые строки, затем конвертируем в строки
        valid_items = [str(item) for item in items if item is not None and str(item).strip() != ""]
        return ", ".join(valid_items)

    return str(items)


def format_similars_with_links(similars: Union[List[str], str, None], name_to_path: Dict[str, str], output_dir: str) -> str:
    """
    Форматирует список похожих структур со ссылками на их файлы.

    Args:
        similars: Список названий похожих структур или строка.
        name_to_path: Словарь, сопоставляющий названия структур с путями к файлам.
        output_dir: Директория, в которой будет сохранен файл README.

    Returns:
        Отформатированная строка со ссылками на похожие структуры, разделенные запятыми.
    """
    if not similars:
        return ""

    result = []
    if isinstance(similars, list):
        for item in similars:
            if item is None or str(item).strip() == "":
                continue

            # Создаем ссылку, если путь существует, иначе просто используем название
            if item in name_to_path:
                # Конвертируем в относительный путь от файла README
                rel_path = os.path.relpath(name_to_path[item], start=output_dir)
                result.append(f"[{item}]({rel_path})")
            else:
                result.append(str(item))
    else:
        # Если это одиночная строка, просто возвращаем ее
        return str(similars)

    return ", ".join(result)


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


def process_yaml_files(yaml_files: List[str]) -> tuple:
    """
    Обрабатывает YAML-файлы для извлечения информации о структурах.

    Args:
        yaml_files: Список путей к YAML-файлам.

    Returns:
        Кортеж (sections, name_to_path)
    """
    sections = defaultdict(list)
    name_to_path = {}
    processed_count = 0
    error_count = 0

    # Счетчики для статистики валидации
    valid_files = 0
    error_files = 0
    warning_files = 0

    # Первый проход - создаем отображение имен на пути
    for file_path in yaml_files:
        try:
            # Пропускаем файлы _meta.yaml
            if os.path.basename(file_path) == "_meta.yaml":
                continue

            data = read_yaml_file(file_path)
            if not data:
                error_count += 1
                error_files += 1
                continue

            name = data.get("name", os.path.basename(file_path).replace(".yaml", ""))
            name_to_path[name] = file_path
            valid_files += 1
        except Exception as e:
            error_count += 1
            error_files += 1
            logger.error(f"Непредвиденная ошибка при обработке {file_path}: {e}")

    # Второй проход - обрабатываем структуры с полным отображением
    for file_path in yaml_files:
        try:
            # Пропускаем файлы _meta.yaml
            if os.path.basename(file_path) == "_meta.yaml":
                continue

            data = read_yaml_file(file_path)
            if not data:
                continue

            # Определяем секцию
            section = os.path.dirname(file_path).replace(f"{SCHLIFFS_DIR}/", "")
            if not section:
                section = "main"

            # Создаем информацию о структуре
            name = data.get("name", os.path.basename(file_path).replace(".yaml", ""))
            structure_info = {
                "name": name,
                "description": data.get("description", ""),
                "description_ru": data.get("description_ru", ""),
                "snow_type": format_snow_types(data.get("snow_type", [])),
                "snow_temperature": data.get("snow_temperature", []),
                "house": data.get("house", ""),
                "country": data.get("country", ""),
                "tags": data.get("tags", []),
                "similars": data.get("similars", []),
                "file_path": file_path,
            }

            sections[section].append(structure_info)
            processed_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Непредвиденная ошибка при обработке {file_path}: {e}")

    logger.info(f"Успешно обработано {processed_count} файлов с {error_count} ошибками")

    # Выводим статистику валидации
    print_validation_summary(valid_files, error_files, warning_files)

    return sections, name_to_path


def collect_structure_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    Собирает данные из всех YAML-файлов структур.

    Returns:
        Словарь с секциями в качестве ключей и списками информации о структурах в качестве значений.
    """
    yaml_files = find_yaml_files(SCHLIFFS_DIR)
    logger.info(f"Найдено {len(yaml_files)} YAML-файлов")

    sections, name_to_path = process_yaml_files(yaml_files)

    # Добавляем ссылку на name_to_path где необходимо
    for section_structures in sections.values():
        for structure in section_structures:
            structure["name_to_path"] = name_to_path

    return sections


def collect_section_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Собирает метаданные для всех секций из файлов _meta.yaml.

    Returns:
        Словарь с именами секций в качестве ключей и их метаданными в качестве значений.
    """
    section_metadata = {}

    # Находим все файлы _meta.yaml в директориях секций
    meta_files = glob.glob(f"{SCHLIFFS_DIR}/*/_meta.yaml")
    logger.info(f"Найдено {len(meta_files)} файлов метаданных секций")

    for meta_file in meta_files:
        # Извлекаем имя секции из пути к директории
        section = os.path.basename(os.path.dirname(meta_file))

        # Читаем метаданные
        metadata = read_yaml_file(meta_file)
        if metadata:
            section_metadata[section] = metadata
            logger.debug(f"Загружены метаданные для секции: {section}")

    return section_metadata


def format_temperature_range(snow_temperature: Union[List[Dict[str, Any]], None]) -> str:
    """
    Форматирует диапазон температуры снега для отображения в таблице в формате "max min".
    Пример: "+3 -3" или "-1 -6"

    Args:
        snow_temperature: Список диапазонов температуры снега.

    Returns:
        Отформатированная строка с диапазоном температуры в формате "max min".
    """
    if not snow_temperature:
        return ""

    try:
        # Берем только первый диапазон (если их несколько)
        temp_range = snow_temperature[0]
        min_temp = temp_range.get("min")
        max_temp = temp_range.get("max")

        # Если min или max отсутствуют, возвращаем пустую строку
        if min_temp is None or max_temp is None:
            return ""

        # Форматируем числа, добавляя + к положительным
        min_temp_str = f"+{min_temp}" if float(min_temp) > 0 else str(min_temp)
        max_temp_str = f"+{max_temp}" if float(max_temp) > 0 else str(max_temp)

        # Убираем .0 в конце для целых чисел
        min_temp_str = min_temp_str.replace('.0', '')
        max_temp_str = max_temp_str.replace('.0', '')

        # Форматируем как "max min"
        result = f"{max_temp_str} {min_temp_str}"
        logger.debug(f"Отформатированный диапазон температуры: {result}")
        return result
    except Exception as e:
        logger.warning(f"Ошибка при форматировании температурного диапазона: {e}")
        return ""


def generate_readme(sections: Dict[str, List[Dict[str, Any]]], header_file: str,
                section_metadata: Dict[str, Dict[str, Any]], language: str = "en",
                sort_by: str = "name", filter_pattern: Optional[str] = None) -> None:
    """
    Генерирует файл README для указанного языка.

    Args:
        sections: Словарь с секциями и данными их структур.
        header_file: Путь к файлу-шаблону заголовка.
        section_metadata: Метаданные для всех секций.
        language: Целевой язык ('en' или 'ru').
        sort_by: Поле для сортировки структур.
        filter_pattern: Регулярное выражение для фильтрации структур.
    """
    # Настраиваем языко-зависимые параметры
    if language == "en":
        output_file = README_FILE
        titles = {
            "main_title": "Steinschliff Structures",
            "description": "This repository contains information about various ski grinding structures.",
            "toc": "Table of Contents",
            "website": "Website",
            "video": "Video Overview",
            "table_headers": ["Name", "Description", "Snow Type", "Temp Range", "Tags", "Similar Structures"],
        }
        description_field = "description"
    else:  # ru
        output_file = README_RU_FILE
        titles = {
            "main_title": "Структуры Steinschliff",
            "description": "Этот репозиторий содержит информацию о различных структурах для шлифовки лыж.",
            "toc": "Оглавление",
            "website": "Сайт",
            "video": "Обзор",
            "table_headers": ["Название", "Описание", "Тип снега", "Температура", "Теги", "Похожие структуры"],
        }
        description_field = "description_ru"

    # Получаем выходную директорию (для вычисления относительных путей)
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if not output_dir:
        output_dir = os.getcwd()

    # Читаем содержимое заголовка
    header_content = read_header_file(header_file)

    with open(output_file, 'w', encoding='utf-8') as f:
        # Записываем содержимое заголовка
        if header_content:
            f.write(header_content)
            # Добавляем перевод строки, если его нет в конце
            if not header_content.endswith('\n'):
                f.write("\n")
            f.write("\n")
        else:
            # Используем заголовок по умолчанию, если пользовательский не предоставлен
            f.write(f"# {titles['main_title']}\n\n")
            f.write(f"{titles['description']}\n\n")

        # Оглавление
        f.write(f"## {titles['toc']}\n\n")
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            section_anchor = section.lower().replace(" ", "-")
            f.write(f"* [{section_title}](#{section_anchor})\n")
        f.write("\n")

        # Секции со структурами
        for section in sorted(sections.keys()):
            section_title = section.capitalize()

            # Добавляем метаданные секции, если доступны
            if section in section_metadata:
                meta = section_metadata[section]

                # Получаем описание на соответствующем языке
                if f"{description_field}" in meta and meta[f"{description_field}"]:
                    section_description = meta[f"{description_field}"]
                else:
                    section_description = meta.get("description", "")

                # Записываем заголовок секции и описание
                f.write(f"## {section_title}\n\n")
                f.write(f"{section_description}\n\n")

                # Добавляем ссылку на сайт, если доступна
                website_url = meta.get("website_url", "")
                if website_url:
                    f.write(f"{titles['website']}: [{meta.get('name', section_title)}]({website_url})\n\n")

                # Добавляем ссылку на видео, если доступна
                video_url = meta.get("video_url", "")
                if video_url:
                    f.write(f"{titles['video']}: [{meta.get('name', section_title)}]({video_url})\n\n")
            else:
                f.write(f"## {section_title}\n\n")

            # Таблица со структурами
            table_headers = titles["table_headers"]
            f.write(f"| {table_headers[0]} | {table_headers[1]} | {table_headers[2]} | {table_headers[3]} | {table_headers[4]} | {table_headers[5]} |\n")
            f.write("|------|------------|-----------|------------|------|-------------------|\n")

            # Используем генератор для потоковой обработки данных без хранения всего в памяти
            def stream_sorted_structures(section_data, sort_field, pattern=None):
                """Функция-генератор для выдачи отсортированных и отфильтрованных структур."""
                # Создаем функцию для получения ключа сортировки
                if sort_field == "name":
                    key_func = lambda x: str(x["name"])
                elif sort_field == "snow_type":
                    key_func = lambda x: str(x["snow_type"])
                elif sort_field == "house":
                    key_func = lambda x: str(x["house"])
                else:
                    key_func = lambda x: str(x["name"])

                # Сортируем структуры
                structures = sorted(section_data, key=key_func)

                # Фильтруем при необходимости
                if pattern:
                    regex = re.compile(pattern, re.IGNORECASE)
                    for structure in structures:
                        if (regex.search(str(structure["name"])) or
                            regex.search(str(structure[description_field])) or
                            regex.search(str(structure["snow_type"]))):
                            yield structure
                else:
                    # Выдаем все структуры
                    for structure in structures:
                        yield structure

            # Потоковая обработка отсортированных и отфильтрованных структур
            for structure in stream_sorted_structures(sections[section], sort_by, filter_pattern):
                # Создаем ссылку от имени к YAML-файлу используя относительный путь
                file_path = structure['file_path']
                rel_path = os.path.relpath(file_path, start=output_dir)
                name_with_link = f"[{structure['name']}]({rel_path})"

                # Форматируем теги и похожие структуры
                tags = format_list_for_display(structure.get('tags', []))
                similars = format_similars_with_links(structure.get('similars', []), structure['name_to_path'], output_dir)

                # Получаем описание на нужном языке
                description = structure[description_field] if structure[description_field] else ""

                # Форматируем диапазон температуры
                temp_range = format_temperature_range(structure.get('snow_temperature', []))

                f.write(f"| {name_with_link} | {description} | {structure['snow_type']} | {temp_range} | {tags} | {similars} |\n")

            f.write("\n")

    logger.info(f"README для языка {language.upper()} успешно сгенерирован в {os.path.abspath(output_file)}")


def validate_yaml_files(directory: str) -> None:
    """
    Запускает проверку всех YAML-файлов на соответствие схемам без генерации README.

    Args:
        directory: Директория для поиска YAML-файлов
    """
    yaml_files = find_yaml_files(directory)
    logger.info(f"Запуск валидации для {len(yaml_files)} YAML-файлов...")

    # Счетчики для статистики валидации
    valid_files = 0
    error_files = 0
    warning_files = 0

    # Список файлов с ошибками для итогового отчета
    files_with_errors = []

    for file_path in yaml_files:
        try:
            filename = os.path.basename(file_path)

            # Для метаданных секций используем модель SectionMetadata
            if filename == "_meta.yaml":
                try:
                    SectionMetadata.model_validate(yaml.safe_load(open(file_path, 'r', encoding='utf-8')))
                    valid_files += 1
                    logger.debug(f"{GREEN}✓{RESET} Файл {file_path} успешно прошел валидацию")
                except ValidationError as e:
                    error_report = format_validation_error(e, file_path)
                    logger.warning(f"\n{error_report}")
                    warning_files += 1
                    files_with_errors.append((file_path, "предупреждение"))
            # Для остальных файлов используем модель SchliffStructure
            else:
                try:
                    data = yaml.safe_load(open(file_path, 'r', encoding='utf-8'))
                    SchliffStructure.model_validate(data)
                    valid_files += 1
                    logger.debug(f"{GREEN}✓{RESET} Файл {file_path} успешно прошел валидацию")
                except ValidationError as e:
                    error_report = format_validation_error(e, file_path)
                    logger.warning(f"\n{error_report}")

                    # Если есть обязательные поля, считаем предупреждением
                    if data and "name" in data and "description" in data:
                        warning_files += 1
                        files_with_errors.append((file_path, "предупреждение"))
                    else:
                        error_files += 1
                        files_with_errors.append((file_path, "ошибка"))
        except Exception as e:
            logger.error(f"{RED}✗{RESET} Ошибка при валидации {file_path}: {e}")
            error_files += 1
            files_with_errors.append((file_path, "ошибка"))

    # Выводим итоговую статистику
    print_validation_summary(valid_files, error_files, warning_files)

    # Выводим список файлов с ошибками, если они есть
    if files_with_errors:
        logger.info(f"\n{BOLD}Список файлов с проблемами:{RESET}")
        for file_path, status in files_with_errors:
            status_color = YELLOW if status == "предупреждение" else RED
            logger.info(f"{status_color}[{status}]{RESET} {file_path}")


def main() -> None:
    """
    Основная функция, которая координирует процесс генерации README.
    """
    parser = argparse.ArgumentParser(description="Генерация файлов README из структур Steinschliff")
    parser.add_argument("--debug", action="store_true", help="Включить подробное логирование")
    parser.add_argument("--config", dest="config_file", help="Путь к файлу конфигурации")
    parser.add_argument("--en-header", dest="en_header_file", help="Путь к шаблону заголовка английского README")
    parser.add_argument("--ru-header", dest="ru_header_file", help="Путь к шаблону заголовка русского README")
    parser.add_argument("--sort-by", choices=["name", "snow_type", "house"], default="name",
                        help="Поле для сортировки структур")
    parser.add_argument("--filter", dest="filter_pattern", help="Фильтрация структур по регулярному выражению")
    parser.add_argument("--exclude-empty", action="store_true", help="Исключить секции без структур")
    parser.add_argument("--validate", action="store_true", help="Только проверить YAML-файлы без генерации README")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Включено подробное логирование")

    # Загрузка конфигурации
    config = load_config(args.config_file)

    # Устанавливаем глобальные переменные на основе конфигурации
    global SCHLIFFS_DIR, README_FILE, README_RU_FILE
    SCHLIFFS_DIR = config["schliffs_dir"]
    README_FILE = config["readme_file"]
    README_RU_FILE = config["readme_ru_file"]
    DEFAULT_EN_HEADER_FILE = config["header_templates"]["en"]
    DEFAULT_RU_HEADER_FILE = config["header_templates"]["ru"]

    # Если запрошена только валидация, выполняем её и выходим
    if args.validate:
        logger.info("Запуск режима валидации YAML-файлов")
        validate_yaml_files(SCHLIFFS_DIR)
        return

    # Переопределяем конфигурацию аргументами командной строки
    if args.en_header_file:
        config["header_templates"]["en"] = args.en_header_file
    if args.ru_header_file:
        config["header_templates"]["ru"] = args.ru_header_file
    if args.sort_by:
        config["sort_field"] = args.sort_by
    if args.filter_pattern:
        config["filter_pattern"] = args.filter_pattern
    if args.exclude_empty:
        config["exclude_empty_sections"] = True

    # Устанавливаем файлы заголовков
    en_header_file = DEFAULT_EN_HEADER_FILE
    ru_header_file = DEFAULT_RU_HEADER_FILE

    # Убеждаемся, что директория для шаблонов существует
    os.makedirs(os.path.dirname(DEFAULT_EN_HEADER_FILE), exist_ok=True)

    # Создаем файлы шаблонов по умолчанию, если они не существуют
    if not os.path.exists(DEFAULT_EN_HEADER_FILE):
        with open(DEFAULT_EN_HEADER_FILE, 'w', encoding='utf-8') as f:
            f.write("# Steinschliff Structures\n\n")
            f.write("This repository contains information about various ski grinding structures.\n\n")
            f.write("*This header content is static and won't be overwritten during README generation.*\n\n")
        logger.info(f"Создан шаблон заголовка английского README по умолчанию в {os.path.abspath(DEFAULT_EN_HEADER_FILE)}")

    if not os.path.exists(DEFAULT_RU_HEADER_FILE):
        with open(DEFAULT_RU_HEADER_FILE, 'w', encoding='utf-8') as f:
            f.write("# Структуры Steinschliff\n\n")
            f.write("Этот репозиторий содержит информацию о различных структурах для шлифовки лыж.\n\n")
            f.write("*Это статический заголовок, который не будет перезаписан при генерации README.*\n\n")
        logger.info(f"Создан шаблон заголовка русского README по умолчанию в {os.path.abspath(DEFAULT_RU_HEADER_FILE)}")

    logger.info("Начало генерации README")
    logger.info(f"Используется заголовок английского README из: {os.path.abspath(en_header_file)}")
    logger.info(f"Используется заголовок русского README из: {os.path.abspath(ru_header_file)}")

    # Сбор данных о структурах
    sections = collect_structure_data()
    logger.info(f"Собраны данные для {sum(len(structures) for structures in sections.values())} структур в {len(sections)} секциях")

    # Сбор метаданных секций
    section_metadata = collect_section_metadata()

    # Генерация файлов README
    generate_readme(sections, en_header_file, section_metadata, "en", config["sort_field"], config["filter_pattern"])
    generate_readme(sections, ru_header_file, section_metadata, "ru", config["sort_field"], config["filter_pattern"])

    logger.info("Генерация README успешно завершена")


if __name__ == "__main__":
    main()