"""
Скрипт для управления переводами в проекте.
"""

import logging
import os
import sys
from pathlib import Path

import typer
from rich.traceback import install as rich_traceback_install

# Добавляем родительскую директорию в sys.path, чтобы можно было импортировать модуль steinschliff
sys.path.insert(0, str(Path(__file__).parent.parent))

from steinschliff.i18n import (
    compile_translations,
    extract_messages,
    get_translation_directory,
    init_locale,
    update_locale,
)
from steinschliff.logging import setup_logging

rich_traceback_install(show_locals=True)
setup_logging(level=logging.INFO)
logger = logging.getLogger("i18n")

app = typer.Typer(help="Управление переводами (i18n)")


@app.command("extract")
def cmd_extract() -> None:
    """Извлечь сообщения для перевода."""
    extract_messages()


@app.command("init")
def cmd_init(
    locale: str = typer.Option(..., "-l", "--locale", help="Код локали (например, ru, en)"),
) -> None:
    """Инициализировать новую локаль."""
    init_locale(locale)


@app.command("update")
def cmd_update(
    locale: str = typer.Option(..., "-l", "--locale", help="Код локали (например, ru, en)"),
) -> None:
    """Обновить существующую локаль."""
    update_locale(locale)


@app.command("update-all")
def cmd_update_all() -> None:
    """Обновить все существующие локали."""
    translations_dir = get_translation_directory()
    locales = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
    if locales:
        for locale in locales:
            logger.info("Обновление локали %s...", locale)
            update_locale(locale)
    else:
        logger.warning("Локали не найдены.")


@app.command("compile")
def cmd_compile() -> None:
    """Скомпилировать переводы."""
    compile_translations()


@app.command("list")
def cmd_list() -> None:
    """Показать список доступных локалей."""
    translations_dir = get_translation_directory()
    locales = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
    if locales:
        logger.info("Доступные локали:")
        for locale in locales:
            logger.info("  - %s", locale)
    else:
        logger.info("Локали не найдены.")


if __name__ == "__main__":
    app()
