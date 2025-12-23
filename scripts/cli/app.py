"""Сборка Typer-приложения и регистрация команд."""

from __future__ import annotations

from typing import Literal

import typer
from rich.traceback import install as rich_traceback_install

from .commands.conditions import register as register_conditions
from .commands.export_csv import register as register_export_csv
from .commands.export_json import register as register_export_json
from .commands.generate import register as register_generate
from .commands.list_cmd import register as register_list
from .common import run_generate, version_callback

rich_traceback_install(show_locals=True)

app = typer.Typer(help="Инструменты генерации README и экспорта данных.", add_completion=True)


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
    _version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Показать версию и выйти",
        rich_help_panel="Отладка",
    ),
) -> None:
    """Если команда не указана — сгенерирует README и экспортирует JSON."""
    _ = extract_messages  # зарезервировано
    if ctx.invoked_subcommand is not None:
        return

    run_generate(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )


# Регистрируем команды:
register_generate(app)
register_export_json(app)
register_list(app)
register_export_csv(app)
register_conditions(app)
