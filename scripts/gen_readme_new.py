"""
Скрипт для генерации README.md из YAML-файлов в директории schliffs.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steinschliff.generator import ReadmeGenerator, export_json
from steinschliff.utils import setup_logging


def main():
    """Основная функция скрипта."""
    parser = argparse.ArgumentParser(description="Генерация README.md из YAML-файлов")
    parser.add_argument("--schliffs-dir", default="schliffs", help="Директория с YAML-файлами (по умолчанию: schliffs)")
    parser.add_argument(
        "--output", default="README_en.md", help="Путь к выходному файлу README на английском (по умолчанию: README.md)"
    )
    parser.add_argument(
        "--output-ru", default="README.md", help="Путь к выходному файлу README на русском (по умолчанию: README.ru.md)"
    )
    parser.add_argument(
        "--sort",
        default="name",
        choices=["name", "rating", "country", "temperature"],
        help="Поле для сортировки структур (по умолчанию: name)",
    )
    parser.add_argument(
        "--translations-dir",
        default="translations",
        help="Директория с JSON-файлами переводов (по умолчанию: translations)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Уровень логирования (по умолчанию: INFO)",
    )
    parser.add_argument(
        "--create-translations", action="store_true", help="Создать пустые файлы переводов, если они не существуют"
    )
    parser.add_argument(
        "--extract-messages",
        action="store_true",
        help="Только извлечь сообщения для перевода и создать шаблон .pot файла",
    )
    args = parser.parse_args()

    # Настраиваем логирование
    setup_logging(level=getattr(logging, args.log_level))
    logger = logging.getLogger("steinschliff")

    # Определяем абсолютные пути
    project_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schliffs_dir = os.path.join(project_dir, args.schliffs_dir)
    output_file = os.path.join(project_dir, args.output)
    output_ru = os.path.join(project_dir, args.output_ru)
    translations_dir = os.path.join(project_dir, args.translations_dir)

    # Создаем директорию для переводов, если её нет
    if not os.path.exists(translations_dir):
        os.makedirs(translations_dir)
        logger.info("Создана директория для переводов: %s", translations_dir)

    # Создаем пустые файлы переводов, если указан флаг
    if args.create_translations:
        for lang in ["en", "ru"]:
            translation_file = os.path.join(translations_dir, f"{lang}.json")
            if not os.path.exists(translation_file):
                with open(translation_file, "w", encoding="utf-8") as f:
                    f.write("{}")
                logger.info("Создан пустой файл перевода: %s", translation_file)

    # Конфигурация для генератора
    config = {
        "schliffs_dir": schliffs_dir,
        "readme_file": output_file,
        "readme_ru_file": output_ru,
        "sort_field": args.sort,
        "translations_dir": translations_dir,
    }

    try:
        # Инициализируем и запускаем генератор README
        generator = ReadmeGenerator(config)
        generator.run()
        logger.info("README успешно сгенерирован: %s и %s", output_file, output_ru)

        # Экспортируем данные в JSON для Astro-сайта
        export_json(generator.services, out_path="webapp/src/data/structures.json")
        logger.info("JSON-данные экспортированы в webapp/src/data/structures.json")
    except Exception:
        logger.exception("Ошибка при генерации README")
        sys.exit(1)


if __name__ == "__main__":
    main()
