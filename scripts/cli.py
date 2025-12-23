"""
Скрипт для генерации README.md из YAML-файлов в директории schliffs.
"""

import csv
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
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as rich_traceback_install

import steinschliff.utils as utils_module
from steinschliff.formatters import format_list_for_display, format_temperature_range
from steinschliff.generator import ReadmeGenerator, export_json
from steinschliff.logging import setup_logging
from steinschliff.models import StructureInfo
from steinschliff.ui.rich import print_kv_panel

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


def _build_generator(
    *,
    schliffs_dir: str,
    output: str,
    output_ru: str,
    sort: Literal["name", "rating", "country", "temperature"],
    translations_dir: str,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    create_translations: bool,
):
    """Собирает конфиг и возвращает (logger, generator, config)."""
    logger, config = _prepare(
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


def _run_generate(
    *,
    schliffs_dir: str,
    output: str,
    output_ru: str,
    sort: Literal["name", "rating", "country", "temperature"],
    translations_dir: str,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    create_translations: bool,
):
    """Общий раннер генерации README и экспорта JSON."""
    logger, generator, config = _build_generator(
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
        export_json(generator.services, out_path="webapp/src/data/structures.json")

        summary = Table.grid(padding=(0, 1))
        summary.add_row("[bold]README EN[/]:", f"[cyan]{config['readme_file']}[/]")
        summary.add_row("[bold]README RU[/]:", f"[cyan]{config['readme_ru_file']}[/]")
        summary.add_row("[bold]JSON[/]:", "[cyan]webapp/src/data/structures.json[/]")
        console.print(Panel.fit(summary, title="Готово", border_style="green"))
    except Exception as err:
        logger.exception("Ошибка при генерации README")
        raise typer.Exit(code=1) from err


def _load_condition_name_ru(condition_key: str) -> str | None:
    """
    Загружает локализованное название (name_ru) для условия снега из файла snow_conditions.

    Args:
        condition_key: Ключ условия (red, blue, violet, etc.)

    Returns:
        Локализованное название или None, если не найдено
    """
    if not condition_key:
        return None

    try:
        project_root = Path(__file__).resolve().parents[1]
        condition_file = project_root / "snow_conditions" / f"{condition_key.lower()}.yaml"

        if condition_file.exists():
            with condition_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict) and "name_ru" in data:
                    return data["name_ru"]
    except (OSError, yaml.YAMLError):
        pass

    return None


def _format_condition(condition: str | None) -> str:
    """
    Форматирует значение condition для отображения.
    Если condition это ключ SnowCondition, пытается получить локализованное название.

    Args:
        condition: Значение поля condition

    Returns:
        Отформатированная строка для отображения
    """
    if not condition:
        return ""

    condition = condition.strip().lower()
    if not condition:
        return ""

    # Пытаемся загрузить локализованное название из файла
    name_ru = _load_condition_name_ru(condition)
    if name_ru:
        return name_ru

    # Fallback на маппинг ключей на русские названия
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


def _build_table_title(
    *,
    generator: ReadmeGenerator,
    selected_services: dict[str, list[StructureInfo]],
    filter_service: str | None = None,
    filter_condition: str | None = None,
) -> str:
    """
    Строит заголовок таблицы на основе применённых фильтров.

    Args:
        generator: Генератор с метаданными сервисов
        selected_services: Отфильтрованные сервисы
        filter_service: Имя сервиса, по которому фильтровали (если был фильтр)
        filter_condition: Условие снега, по которому фильтровали (если был фильтр)

    Returns:
        Сформированный заголовок таблицы
    """
    title_parts = ["Таблица шлифов"]

    # Добавляем имя сервиса, если был фильтр
    if filter_service:
        # Пытаемся найти видимое имя сервиса
        service_name = None
        for service_key in selected_services:
            service_meta = generator.service_metadata.get(service_key)
            if service_meta and service_meta.name:
                service_name = service_meta.name
                break

        if not service_name:
            # Используем исходное значение фильтра с капитализацией
            service_name = filter_service.capitalize()

        title_parts.append(service_name)

    # Добавляем условие снега, если был фильтр
    if filter_condition:
        condition_name = _format_condition(filter_condition)
        if condition_name:
            title_parts.append(f"для {condition_name}")

    return " ".join(title_parts)


def _render_table(
    *,
    generator: ReadmeGenerator,
    selected_services: dict[str, list[StructureInfo]],
    title: str | None = None,
    filter_service: str | None = None,
    filter_condition: str | None = None,
) -> Table:
    """Строит таблицу структур для выбранных сервисов."""
    # Строим заголовок динамически, если не передан явно
    if title is None:
        title = _build_table_title(
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
            condition_str = _format_condition(s.condition)
            table.add_row(visible_service, str(s.name), s.snow_type or "", condition_str, temp_str, similars_str)

    return table


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

    _run_generate(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )


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
    _run_generate(
        schliffs_dir=schliffs_dir,
        output=output,
        output_ru=output_ru,
        sort=sort,
        translations_dir=translations_dir,
        log_level=log_level,
        create_translations=create_translations,
    )


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

    # Строим генератор единообразно
    _, generator, _ = _build_generator(
        schliffs_dir=schliffs_abs,
        output="README_en.md",
        output_ru="README.md",
        sort=sort,
        translations_dir=os.path.join(project_dir, "translations"),
        log_level=log_level,
        create_translations=False,
    )
    try:
        generator.load_structures()
        generator.load_service_metadata()
        export_json(generator.services, out_path=out_path)
        summary = Table.grid(padding=(0, 1))
        summary.add_row("[bold]JSON[/]:", f"[cyan]{out_path}[/]")
        console.print(Panel.fit(summary, title="JSON экспортирован", border_style="blue"))
    except Exception as err:
        logger.exception("Ошибка при экспорте JSON")
        raise typer.Exit(code=1) from err


def _normalize_condition_filter(condition_input: str) -> str:
    """
    Нормализует введенное значение condition для фильтрации.
    Поддерживает ключи (green, red, etc.) и локализованные названия (Зелёный, Красный, etc.).

    Args:
        condition_input: Введенное значение для фильтрации

    Returns:
        Нормализованный ключ condition или пустая строка
    """
    if not condition_input:
        return ""

    condition_input = condition_input.strip().lower()

    # Маппинг локализованных названий на ключи
    localized_to_key = {
        "красный": "red",
        "синий": "blue",
        "фиолетовый": "violet",
        "оранжевый": "orange",
        "зелёный": "green",
        "зеленый": "green",  # альтернативное написание
        "жёлтый": "yellow",
        "желтый": "yellow",  # альтернативное написание
        "розовый": "pink",
        "коричневый": "brown",
    }

    # Проверяем локализованные названия
    if condition_input in localized_to_key:
        return localized_to_key[condition_input]

    # Проверяем, является ли это уже валидным ключом
    valid_keys = ["red", "blue", "violet", "orange", "green", "yellow", "pink", "brown"]
    if condition_input in valid_keys:
        return condition_input

    return condition_input  # Возвращаем как есть, если не найдено


@app.command("list")
def cmd_list(  # noqa: C901
    schliffs_dir: str = typer.Option("schliffs", help="Директория с YAML-файлами"),
    sort: Literal["name", "rating", "country", "temperature"] = typer.Option(
        "temperature", help="Поле сортировки", case_sensitive=False
    ),
    service: str | None = typer.Option(
        None,
        "-s",
        "--service",
        help="Фильтр по производителю/сервису (например: Ramsau)",
        show_default=False,
    ),
    condition: str | None = typer.Option(
        None,
        "-c",
        "--condition",
        help=(
            "Фильтр по условиям снега (green, red, blue, violet, orange, yellow, pink, "
            "brown или локализованные названия)"
        ),
        show_default=False,
    ),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "INFO", help="Уровень логирования", case_sensitive=False
    ),
):
    """Показать таблицу шлифов. Можно отфильтровать по конкретному производителю и условиям снега."""
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

        # Подготовим маппинг видимого имени сервиса (из _meta.yaml) -> ключ сервиса
        service_name_to_key: dict[str, str] = {}
        for key, meta in generator.service_metadata.items():
            visible_name = (meta.name or key).strip()
            service_name_to_key[visible_name.lower()] = key

        # Определим список сервисов для показа (как обычный dict для типизации)
        selected_services: dict[str, list[StructureInfo]] = dict(generator.services)
        if service:
            lookup = service.strip().lower()
            # Поддержка поиска по ключу директории и по видимому имени
            if lookup in selected_services:
                resolved_key = lookup
            else:
                mapped = service_name_to_key.get(lookup)
                if mapped is None:
                    console.print(Panel.fit(f"Сервис '{service}' не найден", border_style="red"))
                    raise typer.Exit(code=1)
                resolved_key = mapped

            if resolved_key not in selected_services:
                console.print(Panel.fit(f"Сервис '{service}' не найден", border_style="red"))
                raise typer.Exit(code=1)

            selected_services = {resolved_key: selected_services[resolved_key]}

        # Фильтрация по condition
        normalized_condition = None
        if condition:
            normalized_condition = _normalize_condition_filter(condition)
            if not normalized_condition:
                console.print(
                    Panel.fit(
                        (
                            f"Неизвестное условие '{condition}'. Допустимые: red, blue, violet, "
                            "orange, green, yellow, pink, brown"
                        ),
                        border_style="red",
                    )
                )
                raise typer.Exit(code=1)

            # Фильтруем структуры по condition
            filtered_services: dict[str, list[StructureInfo]] = {}
            for service_key, structures in selected_services.items():
                filtered_structures = [
                    s for s in structures if s.condition and s.condition.strip().lower() == normalized_condition
                ]
                if filtered_structures:
                    filtered_services[service_key] = filtered_structures

            if not filtered_services:
                console.print(Panel.fit(f"Не найдено структур с условием '{condition}'", border_style="yellow"))
                raise typer.Exit(code=0)

            selected_services = filtered_services

        table = _render_table(
            generator=generator,
            selected_services=selected_services,
            filter_service=service,
            filter_condition=normalized_condition if condition else None,
        )
        console.print(table)
    except Exception as err:
        logger.exception("Ошибка при построении списка")
        raise typer.Exit(code=1) from err


@app.command("export-csv")
def cmd_export_csv(  # noqa: C901
    schliffs_dir: str = typer.Option("schliffs", help="Директория с YAML-файлами"),
    sort: Literal["name", "rating", "country", "temperature"] = typer.Option(
        "temperature", help="Поле сортировки", case_sensitive=False
    ),
    service: str | None = typer.Option(
        None,
        "-s",
        "--service",
        help="Фильтр по производителю/сервису (например: Ramsau)",
        show_default=False,
    ),
    condition: str | None = typer.Option(
        None,
        "-c",
        "--condition",
        help="Фильтр по условиям снега (green, red, blue, violet, orange, yellow, pink, brown)",
        show_default=False,
    ),
    output: str | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Путь к выходному CSV-файлу (по умолчанию stdout)",
        show_default=False,
    ),
    quiet: bool = typer.Option(
        False,
        "-q",
        "--quiet",
        help="Подавить вывод прогресса (автоматически при выводе в stdout)",
    ),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "WARNING", help="Уровень логирования", case_sensitive=False
    ),
):
    """Экспортировать таблицу шлифов в формате CSV."""
    # Если вывод в stdout - автоматически включаем тихий режим
    if output is None:
        quiet = True

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
        # В тихом режиме подавляем весь rich вывод
        if quiet:
            devnull_console = Console(file=io.StringIO(), quiet=True)
            utils_module.console = devnull_console

        generator = ReadmeGenerator(config)

        # Загружаем структуры с подавлением вывода в тихом режиме
        if quiet:
            # Подавляем вывод Rich Progress через замену stdout
            original_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                generator.load_structures()
                generator.load_service_metadata()
            finally:
                sys.stdout = original_stdout
        else:
            generator.load_structures()
            generator.load_service_metadata()

        # Маппинг видимого имени сервиса -> ключ сервиса
        service_name_to_key: dict[str, str] = {}
        for key, meta in generator.service_metadata.items():
            visible_name = (meta.name or key).strip()
            service_name_to_key[visible_name.lower()] = key

        selected_services: dict[str, list[StructureInfo]] = dict(generator.services)

        # Фильтрация по сервису
        if service:
            lookup = service.strip().lower()
            if lookup in selected_services:
                resolved_key = lookup
            else:
                mapped = service_name_to_key.get(lookup)
                if mapped is None:
                    console.print(Panel.fit(f"Сервис '{service}' не найден", border_style="red"))
                    raise typer.Exit(code=1)
                resolved_key = mapped

            if resolved_key not in selected_services:
                console.print(Panel.fit(f"Сервис '{service}' не найден", border_style="red"))
                raise typer.Exit(code=1)

            selected_services = {resolved_key: selected_services[resolved_key]}

        # Фильтрация по condition
        if condition:
            normalized_condition = _normalize_condition_filter(condition)
            if not normalized_condition:
                console.print(
                    Panel.fit(
                        f"Неизвестное условие '{condition}'. "
                        "Допустимые: red, blue, violet, orange, green, yellow, pink, brown",
                        border_style="red",
                    )
                )
                raise typer.Exit(code=1)

            filtered_services: dict[str, list[StructureInfo]] = {}
            for service_key, structures in selected_services.items():
                filtered_structures = [
                    s for s in structures if s.condition and s.condition.strip().lower() == normalized_condition
                ]
                if filtered_structures:
                    filtered_services[service_key] = filtered_structures

            if not filtered_services:
                console.print(Panel.fit(f"Не найдено структур с условием '{condition}'", border_style="yellow"))
                raise typer.Exit(code=0)

            selected_services = filtered_services

        # Генерация CSV
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)

        # Заголовок
        writer.writerow(["Сервис", "Имя", "Тип снега", "Условия", "Температура", "Похожие"])

        # Данные
        for service_key, items in selected_services.items():
            sorted_items = sorted(items, key=generator._get_structure_sort_key)
            service_meta = generator.service_metadata.get(service_key)
            visible_service = (
                (service_meta.name or service_key) if (service_meta and service_meta.name) else service_key
            )

            for s in sorted_items:
                temp_str = format_temperature_range(s.temperature)
                similars_str = format_list_for_display(s.similars)
                condition_str = _format_condition(s.condition)
                writer.writerow(
                    [visible_service, str(s.name), s.snow_type or "", condition_str, temp_str, similars_str]
                )

        csv_content = csv_buffer.getvalue()

        # Вывод
        if output:
            output_path = Path(output)
            output_path.write_text(csv_content, encoding="utf-8")
            console.print(Panel.fit(f"CSV экспортирован в [cyan]{output}[/cyan]", border_style="green"))
        else:
            sys.stdout.write(csv_content)

    except typer.Exit:
        raise
    except Exception as err:
        logger.exception("Ошибка при экспорте CSV")
        raise typer.Exit(code=1) from err


@app.command("conditions")
def cmd_conditions(  # noqa: C901
    schliffs_dir: str = typer.Option(
        "schliffs",
        "--schliffs",
        "-s",
        help="Путь к директории со шлифами",
    ),
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = typer.Option(
        "WARNING",
        "--log-level",
        "-l",
        help="Уровень логирования",
    ),
):
    """Показать статистику по условиям снега (snow conditions)."""
    setup_logging(level=getattr(logging, log_level))
    logger = logging.getLogger("steinschliff")

    project_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schliffs_abs = os.path.join(project_dir, schliffs_dir)

    config = {
        "schliffs_dir": schliffs_abs,
        "readme_file": "README_en.md",
        "readme_ru_file": "README.md",
        "sort_field": "name",
        "translations_dir": os.path.join(project_dir, "translations"),
    }

    try:
        generator = ReadmeGenerator(config)
        generator.load_structures()

        # Подсчитываем статистику
        condition_counts: Counter[str] = Counter()
        total_structures = 0

        for service_structures in generator.services.values():
            for structure in service_structures:
                total_structures += 1
                if structure.condition:
                    condition_counts[structure.condition.strip().lower()] += 1

        # Загружаем информацию о условиях из snow_conditions
        conditions_info = {}
        snow_conditions_dir = project_dir / "snow_conditions"

        if snow_conditions_dir.exists():
            for condition_file in snow_conditions_dir.glob("*.yaml"):
                try:
                    with condition_file.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        if isinstance(data, dict):
                            key = data.get("key", condition_file.stem)
                            conditions_info[key] = {
                                "name_ru": data.get("name_ru", key),
                                "color": data.get("color", ""),
                                "temperature": data.get("temperature"),
                            }
                except Exception:  # noqa: BLE001
                    pass

        # Маппинг цветов на эмодзи
        color_emoji = {
            "green": "🟢",
            "blue": "🔵",
            "violet": "🟣",
            "orange": "🟠",
            "red": "🔴",
            "pink": "💗",
            "yellow": "💛",
            "brown": "🟤",
        }

        # Создаем таблицу
        table = Table(
            title="📊 Статистика по условиям снега",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )

        table.add_column("Условие", style="bold", justify="left")
        table.add_column("Emoji", justify="center")
        table.add_column("Название", justify="left")
        table.add_column("Температура", style="yellow")
        table.add_column("Количество", justify="right", style="bold green")
        table.add_column("%", justify="right")

        # Сортируем условия по количеству (убывание)
        sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)

        for condition_key, count in sorted_conditions:
            info = conditions_info.get(condition_key, {})
            emoji = color_emoji.get(condition_key, "⚪")
            name_ru = info.get("name_ru", condition_key.capitalize())

            # Форматируем температуру
            temp = info.get("temperature")
            temp_str = format_temperature_range(temp) if temp and isinstance(temp, list) and len(temp) > 0 else "любая"

            percentage = (count / total_structures * 100) if total_structures > 0 else 0

            table.add_row(
                condition_key.upper(),
                emoji,
                name_ru,
                temp_str,
                str(count),
                f"{percentage:.1f}%",
            )

        # Добавляем итоговую строку
        table.add_section()
        table.add_row(
            "[bold]ВСЕГО[/bold]",
            "",
            "",
            "",
            f"[bold]{total_structures}[/bold]",
            "[bold]100.0%[/bold]",
        )

        console.print()
        console.print(table)
        console.print()

        # Дополнительная информация
        if total_structures > 0:
            empty_conditions = total_structures - sum(condition_counts.values())
            if empty_conditions > 0:
                console.print(f"[yellow]⚠️  Структур без condition: {empty_conditions}[/yellow]")
            else:
                console.print("[green]✅ Все структуры имеют валидные значения condition![/green]")

    except Exception as err:
        logger.exception("Ошибка при получении статистики")
        raise typer.Exit(code=1) from err


if __name__ == "__main__":
    app()
