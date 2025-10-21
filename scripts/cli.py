"""
Скрипт для генерации README.md из YAML-файлов в директории schliffs.
"""

import logging
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as rich_traceback_install

# Добавляем родительскую директорию в путь для импорта до локальных импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steinschliff.generator import ReadmeGenerator, export_json
from steinschliff.utils import print_kv_panel, setup_logging

rich_traceback_install(show_locals=True)

app = typer.Typer(help="Инструменты генерации README и экспорта данных.", add_completion=True)
console = Console()

try:
    APP_VERSION = pkg_version("steinschliff")
except PackageNotFoundError:
    APP_VERSION = "dev"


def _version_callback(value: bool):
    if value:
        console.print(f"Steinschliff CLI [bold]{APP_VERSION}[/]")
        raise typer.Exit()


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
        print_kv_panel("Переводы", [("Создана директория", translations_abs)], border_style="blue")

    if create_translations:
        for lang in ["en", "ru"]:
            translation_file = os.path.join(translations_abs, f"{lang}.json")
            if not os.path.exists(translation_file):
                with open(translation_file, "w", encoding="utf-8") as f:
                    f.write("{}")
                print_kv_panel("Переводы", [("Создан файл", translation_file)], border_style="blue")

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
    schliffs_dir: str = typer.Option(
        "schliffs",
        help="Директория с YAML-файлами",
        envvar="STEINSCHLIFF_SCHLIFFS_DIR",
        rich_help_panel="Основные",
    ),
    output: str = typer.Option(
        "README_en.md",
        help="Выходной README на английском",
        envvar="STEINSCHLIFF_README_EN",
        rich_help_panel="Вывод",
    ),
    output_ru: str = typer.Option(
        "README.md",
        help="Выходной README на русском",
        envvar="STEINSCHLIFF_README_RU",
        rich_help_panel="Вывод",
    ),
    sort: Literal["name", "rating", "country", "temperature"] = typer.Option(
        "name",
        help="Поле сортировки",
        case_sensitive=False,
        rich_help_panel="Основные",
    ),
    translations_dir: str = typer.Option(
        "translations",
        help="Директория переводов",
        envvar="STEINSCHLIFF_TRANSLATIONS_DIR",
        rich_help_panel="Основные",
    ),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "INFO",
        help="Уровень логирования",
        case_sensitive=False,
        rich_help_panel="Отладка",
    ),
    create_translations: bool = typer.Option(
        False,
        help="Создать пустые файлы переводов, если нет",
        rich_help_panel="Основные",
    ),
    extract_messages: bool = typer.Option(
        False,
        help="Только извлечь сообщения для перевода (зарезервировано)",
        rich_help_panel="Отладка",
    ),
    version: bool = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Показать версию и выйти",
        rich_help_panel="Отладка",
    ),
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
        export_json(generator.services, out_path="webapp/src/data/structures.json")

        summary = Table.grid(padding=(0, 1))
        summary.add_row("[bold]README EN[/]:", f"[cyan]{config['readme_file']}[/]")
        summary.add_row("[bold]README RU[/]:", f"[cyan]{config['readme_ru_file']}[/]")
        summary.add_row("[bold]JSON[/]:", "[cyan]webapp/src/data/structures.json[/]")
        console.print(Panel.fit(summary, title="Готово", border_style="green"))
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
        export_json(generator.services, out_path="webapp/src/data/structures.json")

        summary = Table.grid(padding=(0, 1))
        summary.add_row("[bold]README EN[/]:", f"[cyan]{config['readme_file']}[/]")
        summary.add_row("[bold]README RU[/]:", f"[cyan]{config['readme_ru_file']}[/]")
        summary.add_row("[bold]JSON[/]:", "[cyan]webapp/src/data/structures.json[/]")
        console.print(Panel.fit(summary, title="Готово", border_style="green"))
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
        summary = Table.grid(padding=(0, 1))
        summary.add_row("[bold]JSON[/]:", f"[cyan]{out_path}[/]")
        console.print(Panel.fit(summary, title="JSON экспортирован", border_style="blue"))
    except Exception:
        logger.exception("Ошибка при экспорте JSON")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
