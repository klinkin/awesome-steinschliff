"""
Скрипт для генерации README.md из YAML-файлов в директории schliffs.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Literal

import typer
from rich.traceback import install as rich_traceback_install

# Добавляем родительскую директорию в путь для импорта до локальных импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steinschliff.generator import ReadmeGenerator, export_json
from steinschliff.utils import setup_logging

rich_traceback_install(show_locals=True)

app = typer.Typer(help="Инструменты генерации README и экспорта данных.")


def _prepare(
    schliffs_dir: str,
    output: str,
    output_ru: str,
    sort: Literal["name", "rating", "country", "temperature"],
    translations_dir: str,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    create_translations: bool,
):
    setup_logging(level=getattr(logging, log_level))
    logger = logging.getLogger("steinschliff")

    project_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schliffs_abs = os.path.join(project_dir, schliffs_dir)
    output_en_abs = os.path.join(project_dir, output)
    output_ru_abs = os.path.join(project_dir, output_ru)
    translations_abs = os.path.join(project_dir, translations_dir)

    if not os.path.exists(translations_abs):
        os.makedirs(translations_abs)
        logger.info("Создана директория для переводов: %s", translations_abs)

    if create_translations:
        for lang in ["en", "ru"]:
            translation_file = os.path.join(translations_abs, f"{lang}.json")
            if not os.path.exists(translation_file):
                with open(translation_file, "w", encoding="utf-8") as f:
                    f.write("{}")
                logger.info("Создан пустой файл перевода: %s", translation_file)

    config = {
        "schliffs_dir": schliffs_abs,
        "readme_file": output_en_abs,
        "readme_ru_file": output_ru_abs,
        "sort_field": sort,
        "translations_dir": translations_abs,
    }

    return logger, config


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    schliffs_dir: str = typer.Option("schliffs", help="Директория с YAML-файлами"),
    output: str = typer.Option("README_en.md", help="Выходной README на английском"),
    output_ru: str = typer.Option("README.md", help="Выходной README на русском"),
    sort: Literal["name", "rating", "country", "temperature"] = typer.Option(
        "name", help="Поле сортировки", case_sensitive=False
    ),
    translations_dir: str = typer.Option("translations", help="Директория переводов"),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "INFO", help="Уровень логирования", case_sensitive=False
    ),
    create_translations: bool = typer.Option(False, help="Создать пустые файлы переводов, если нет"),
    extract_messages: bool = typer.Option(False, help="Только извлечь сообщения для перевода (зарезервировано)"),
):
    """Если команда не указана — сгенерирует README и экспортирует JSON."""
    _ = extract_messages  # зарезервировано
    if ctx.invoked_subcommand is not None:
        return

    logger, config = _prepare(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )

    try:
        generator = ReadmeGenerator(config)
        generator.run()
        logger.info("README успешно сгенерирован: %s и %s", config["readme_file"], config["readme_ru_file"])
        export_json(generator.services, out_path="webapp/src/data/structures.json")
        logger.info("JSON-данные экспортированы в webapp/src/data/structures.json")
    except Exception:
        logger.exception("Ошибка при генерации README")
        raise typer.Exit(code=1)


@app.command("generate")
def cmd_generate(
    schliffs_dir: str = typer.Option("schliffs", help="Директория с YAML-файлами"),
    output: str = typer.Option("README_en.md", help="Выходной README на английском"),
    output_ru: str = typer.Option("README.md", help="Выходной README на русском"),
    sort: Literal["name", "rating", "country", "temperature"] = typer.Option(
        "name", help="Поле сортировки", case_sensitive=False
    ),
    translations_dir: str = typer.Option("translations", help="Директория переводов"),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "INFO", help="Уровень логирования", case_sensitive=False
    ),
    create_translations: bool = typer.Option(False, help="Создать пустые файлы переводов, если нет"),
):
    """Сгенерировать README (EN и RU) и экспортировать JSON."""
    logger, config = _prepare(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )
    try:
        generator = ReadmeGenerator(config)
        generator.run()
        logger.info("README успешно сгенерирован: %s и %s", config["readme_file"], config["readme_ru_file"])
        export_json(generator.services, out_path="webapp/src/data/structures.json")
        logger.info("JSON-данные экспортированы в webapp/src/data/structures.json")
    except Exception:
        logger.exception("Ошибка при генерации README")
        raise typer.Exit(code=1)


@app.command("export-json")
def cmd_export_json(
    schliffs_dir: str = typer.Option("schliffs", help="Директория с YAML-файлами"),
    sort: Literal["name", "rating", "country", "temperature"] = typer.Option(
        "name", help="Поле сортировки", case_sensitive=False
    ),
    out_path: str = typer.Option("webapp/src/data/structures.json", help="Путь для JSON"),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "INFO", help="Уровень логирования", case_sensitive=False
    ),
):
    """Только экспорт JSON-данных для веб-приложения."""
    setup_logging(level=getattr(logging, log_level))
    logger = logging.getLogger("steinschliff")

    project_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schliffs_abs = os.path.join(project_dir, schliffs_dir)

    config = {
        "schliffs_dir": schliffs_abs,
        "readme_file": "README_en.md",
        "readme_ru_file": "README.md",
        "sort_field": sort,
        "translations_dir": os.path.join(project_dir, "translations"),
    }
    try:
        generator = ReadmeGenerator(config)
        generator.load_structures()
        generator.load_service_metadata()
        export_json(generator.services, out_path=out_path)
        logger.info("JSON-данные экспортированы в %s", out_path)
    except Exception:
        logger.exception("Ошибка при экспорте JSON")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
