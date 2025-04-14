#!/usr/bin/env python
"""
Скрипт для управления переводами в проекте.
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Добавляем родительскую директорию в sys.path, чтобы можно было импортировать модуль steinschliff
sys.path.insert(0, str(Path(__file__).parent.parent))

from steinschliff.i18n import (
    extract_messages,
    init_locale,
    update_locale,
    compile_translations,
    get_translation_directory
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("i18n")


def main():
    parser = argparse.ArgumentParser(description='Управление переводами в проекте steinschliff')
    subparsers = parser.add_subparsers(dest='command', help='Команда для выполнения')

    # Извлечение сообщений
    extract_parser = subparsers.add_parser('extract', help='Извлечь сообщения для перевода')

    # Инициализация локали
    init_parser = subparsers.add_parser('init', help='Инициализировать новую локаль')
    init_parser.add_argument('-l', '--locale', required=True, help='Код локали (например, ru, en)')

    # Обновление локали
    update_parser = subparsers.add_parser('update', help='Обновить существующую локаль')
    update_parser.add_argument('-l', '--locale', required=True, help='Код локали (например, ru, en)')

    # Обновление всех локалей
    update_all_parser = subparsers.add_parser('update-all', help='Обновить все существующие локали')

    # Компиляция переводов
    compile_parser = subparsers.add_parser('compile', help='Скомпилировать переводы')

    # Показать список доступных локалей
    list_parser = subparsers.add_parser('list', help='Показать список доступных локалей')

    args = parser.parse_args()

    if args.command == 'extract':
        extract_messages()
    elif args.command == 'init':
        init_locale(args.locale)
    elif args.command == 'update':
        update_locale(args.locale)
    elif args.command == 'update-all':
        translations_dir = get_translation_directory()
        locales = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
        if locales:
            for locale in locales:
                logger.info(f"Обновление локали {locale}...")
                update_locale(locale)
        else:
            logger.warning("Локали не найдены.")
    elif args.command == 'compile':
        compile_translations()
    elif args.command == 'list':
        translations_dir = get_translation_directory()
        locales = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
        if locales:
            print("Доступные локали:")
            for locale in locales:
                print(f"  - {locale}")
        else:
            print("Локали не найдены.")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()