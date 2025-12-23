"""Общие утилиты и shared-логика для CLI.

Сюда складываем только то, что используется несколькими командами.
"""

from __future__ import annotations

import io
import logging
import os
import sys
from collections import Counter
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import steinschliff.utils as utils_module
from steinschliff.export.json import export_structures_json
from steinschliff.formatters import format_list_for_display, format_temperature_range
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging
from steinschliff.models import StructureInfo
from steinschliff.snow_conditions import get_condition_info, get_name_ru, get_valid_keys, normalize_condition_input
from steinschliff.ui.rich import print_kv_panel

console = Console()

try:
    APP_VERSION = pkg_version("steinschliff")
except PackageNotFoundError:
    APP_VERSION = "dev"

PROJECT_ROOT = Path(__file__).resolve().parents[2]


SortField = Literal["name", "rating", "country", "temperature"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def version_callback(value: bool) -> None:
    if value:
        console.print(f"Steinschliff CLI [bold]{APP_VERSION}[/]")
        raise typer.Exit()


def prepare_config(
    *,
    schliffs_dir: str,
    output: str,
    output_ru: str,
    sort: SortField,
    translations_dir: str,
    log_level: LogLevel,
    create_translations: bool,
) -> tuple[logging.Logger, dict[str, str | SortField]]:
    setup_logging(level=getattr(logging, log_level))
    logger = logging.getLogger("steinschliff")

    project_dir = PROJECT_ROOT
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

    config: dict[str, str | SortField] = {
        "schliffs_dir": schliffs_abs,
        "readme_file": output_en_abs,
        "readme_ru_file": output_ru_abs,
        "sort_field": sort,
        "translations_dir": translations_abs,
    }

    return logger, config


def build_generator(
    *,
    schliffs_dir: str,
    output: str,
    output_ru: str,
    sort: SortField,
    translations_dir: str,
    log_level: LogLevel,
    create_translations: bool,
) -> tuple[logging.Logger, ReadmeGenerator, dict[str, str | SortField]]:
    """Собирает конфиг и возвращает (logger, generator, config)."""
    logger, config = prepare_config(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )
    generator = ReadmeGenerator(config)
    return logger, generator, config


def run_generate(
    *,
    schliffs_dir: str,
    output: str,
    output_ru: str,
    sort: SortField,
    translations_dir: str,
    log_level: LogLevel,
    create_translations: bool,
) -> None:
    """Общий раннер генерации README и экспорта JSON."""
    logger, generator, config = build_generator(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )
    try:
        generator.run()
        export_structures_json(services=generator.services, out_path="webapp/src/data/structures.json")

        summary = Table.grid(padding=(0, 1))
        summary.add_row("[bold]README EN[/]:", f"[cyan]{config['readme_file']}[/]")
        summary.add_row("[bold]README RU[/]:", f"[cyan]{config['readme_ru_file']}[/]")
        summary.add_row("[bold]JSON[/]:", "[cyan]webapp/src/data/structures.json[/]")
        console.print(Panel.fit(summary, title="Готово", border_style="green"))
    except Exception as err:
        logger.exception("Ошибка при генерации README")
        raise typer.Exit(code=1) from err


def format_condition(condition: str | None) -> str:
    """Форматирует condition для отображения (RU-название при наличии)."""
    if not condition:
        return ""

    condition = condition.strip().lower()
    if not condition:
        return ""

    name_ru = get_name_ru(condition)
    if name_ru:
        return name_ru

    condition_names = {
        "red": "Красный",
        "blue": "Синий",
        "violet": "Фиолетовый",
        "orange": "Оранжевый",
        "green": "Зелёный",
        "yellow": "Жёлтый",
        "pink": "Розовый",
        "brown": "Коричневый",
    }

    return condition_names.get(condition, condition.capitalize())


def build_table_title(
    *,
    generator: ReadmeGenerator,
    selected_services: dict[str, list[StructureInfo]],
    filter_service: str | None = None,
    filter_condition: str | None = None,
) -> str:
    """Строит заголовок таблицы на основе применённых фильтров."""
    title_parts = ["Таблица шлифов"]

    if filter_service:
        service_name = None
        for service_key in selected_services:
            service_meta = generator.service_metadata.get(service_key)
            if service_meta and service_meta.name:
                service_name = service_meta.name
                break

        if not service_name:
            service_name = filter_service.capitalize()

        title_parts.append(service_name)

    if filter_condition:
        condition_name = format_condition(filter_condition)
        if condition_name:
            title_parts.append(f"для {condition_name}")

    return " ".join(title_parts)


def render_table(
    *,
    generator: ReadmeGenerator,
    selected_services: dict[str, list[StructureInfo]],
    title: str | None = None,
    filter_service: str | None = None,
    filter_condition: str | None = None,
) -> Table:
    """Строит таблицу структур для выбранных сервисов."""
    if title is None:
        title = build_table_title(
            generator=generator,
            selected_services=selected_services,
            filter_service=filter_service,
            filter_condition=filter_condition,
        )

    table = Table(title=title, show_lines=False)
    table.add_column("Сервис", style="cyan", no_wrap=True)
    table.add_column("Имя", style="bold", no_wrap=True)
    table.add_column("Тип снега", style="magenta")
    table.add_column("Условия", style="green")
    table.add_column("Температура", style="yellow")
    table.add_column("Похожие", style="green")

    for service_key, items in selected_services.items():
        sorted_items = sorted(items, key=generator._get_structure_sort_key)
        service_meta = generator.service_metadata.get(service_key)
        visible_service = (service_meta.name or service_key) if (service_meta and service_meta.name) else service_key
        for s in sorted_items:
            temp_str = format_temperature_range(s.temperature)
            similars_str = format_list_for_display(s.similars)
            condition_str = format_condition(s.condition)
            table.add_row(visible_service, str(s.name), s.snow_type or "", condition_str, temp_str, similars_str)

    return table


def normalize_condition_filter(condition_input: str) -> str:
    """Нормализует condition для фильтрации (ключи/цвета/синонимы из snow_conditions)."""
    return normalize_condition_input(condition_input)


def load_generator_for_reporting(
    *,
    schliffs_dir: str,
    sort: SortField,
    log_level: LogLevel,
) -> ReadmeGenerator:
    """Упрощённый билдер генератора для read-only команд (list/export-csv/conditions)."""
    setup_logging(level=getattr(logging, log_level))
    project_dir = PROJECT_ROOT
    schliffs_abs = os.path.join(project_dir, schliffs_dir)

    config = {
        "schliffs_dir": schliffs_abs,
        "readme_file": "README_en.md",
        "readme_ru_file": "README.md",
        "sort_field": sort,
        "translations_dir": os.path.join(project_dir, "translations"),
    }
    generator = ReadmeGenerator(config)
    generator.load_structures()
    generator.load_service_metadata()
    return generator


def compute_conditions_stats(
    *,
    schliffs_dir: str,
    log_level: LogLevel,
) -> tuple[int, Counter[str], dict[str, dict[str, object]]]:
    """Собирает статистику по snow conditions из YAML + справочника snow_conditions."""
    setup_logging(level=getattr(logging, log_level))
    project_dir = PROJECT_ROOT
    schliffs_abs = os.path.join(project_dir, schliffs_dir)

    config = {
        "schliffs_dir": schliffs_abs,
        "readme_file": "README_en.md",
        "readme_ru_file": "README.md",
        "sort_field": "name",
        "translations_dir": os.path.join(project_dir, "translations"),
    }

    generator = ReadmeGenerator(config)
    generator.load_structures()

    condition_counts: Counter[str] = Counter()
    total_structures = 0

    for service_structures in generator.services.values():
        for structure in service_structures:
            total_structures += 1
            if structure.condition:
                condition_counts[structure.condition.strip().lower()] += 1

    conditions_info: dict[str, dict[str, object]] = {}
    for key in get_valid_keys():
        info = get_condition_info(key) or {}
        conditions_info[key] = {
            "name_ru": info.get("name_ru", key),
            "color": info.get("color", ""),
            "temperature": info.get("temperature"),
        }

    return total_structures, condition_counts, conditions_info


def maybe_silence_rich_output(quiet: bool) -> None:
    """В quiet-режиме подавляем rich-вывод в utils_module."""
    if quiet:
        devnull_console = Console(file=io.StringIO(), quiet=True)
        utils_module.console = devnull_console


def maybe_silence_progress_output(quiet: bool) -> tuple[io.StringIO | None, object | None]:
    """В quiet-режиме подавляем вывод прогресс-бара заменой stdout."""
    if not quiet:
        return None, None

    original_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    return new_stdout, original_stdout


def restore_stdout(original_stdout: object | None) -> None:
    if original_stdout is not None:
        sys.stdout = original_stdout  # type: ignore[assignment]
