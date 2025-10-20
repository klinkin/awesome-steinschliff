"""
Скрипт для управления переводами в проекте.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Добавляем родительскую директорию в sys.path, чтобы можно было импортировать модуль steinschliff
sys.path.insert(0, str(Path(__file__).parent.parent))

from steinschliff.i18n import (
    compile_translations,
    extract_messages,
    get_translation_directory,
    init_locale,
    update_locale,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("i18n")


def _cmd_extract(_args) -> None:
    extract_messages()


def _cmd_init(args) -> None:
    init_locale(args.locale)


def _cmd_update(args) -> None:
    update_locale(args.locale)


def _cmd_update_all(_args) -> None:
    translations_dir = get_translation_directory()
    locales = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
    if locales:
        for locale in locales:
            logger.info("Обновление локали %s...", locale)
            update_locale(locale)
    else:
        logger.warning("Локали не найдены.")


def _cmd_compile(_args) -> None:
    compile_translations()


def _cmd_list(_args) -> None:
    translations_dir = get_translation_directory()
    locales = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
    if locales:
        logger.info("Доступные локали:")
        for locale in locales:
            logger.info("  - %s", locale)
    else:
        logger.info("Локали не найдены.")


def main():
    parser = argparse.ArgumentParser(description="Управление переводами в проекте steinschliff")
    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")

    # Извлечение сообщений
    subparsers.add_parser("extract", help="Извлечь сообщения для перевода")

    # Инициализация локали
    init_parser = subparsers.add_parser("init", help="Инициализировать новую локаль")
    init_parser.add_argument("-l", "--locale", required=True, help="Код локали (например, ru, en)")

    # Обновление локали
    update_parser = subparsers.add_parser("update", help="Обновить существующую локаль")
    update_parser.add_argument("-l", "--locale", required=True, help="Код локали (например, ru, en)")

    # Обновление всех локалей
    subparsers.add_parser("update-all", help="Обновить все существующие локали")

    # Компиляция переводов
    subparsers.add_parser("compile", help="Скомпилировать переводы")

    # Показать список доступных локалей
    subparsers.add_parser("list", help="Показать список доступных локалей")

    args = parser.parse_args()

    dispatch = {
        "extract": _cmd_extract,
        "init": _cmd_init,
        "update": _cmd_update,
        "update-all": _cmd_update_all,
        "compile": _cmd_compile,
        "list": _cmd_list,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return
    handler(args)


if __name__ == "__main__":
    main()
