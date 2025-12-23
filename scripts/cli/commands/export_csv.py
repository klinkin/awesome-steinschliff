from __future__ import annotations

import io
import logging
import os
import sys
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel

import steinschliff.utils as utils_module
from scripts.cli.common import PROJECT_ROOT, console, normalize_condition_filter, restore_stdout
from scripts.cli.error_handler import handle_user_errors
from steinschliff.catalog import filter_services_by_condition, select_services
from steinschliff.config import GeneratorConfig
from steinschliff.exceptions import SteinschliffUserError
from steinschliff.export.csv import export_structures_csv_string
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging
from steinschliff.snow_conditions import get_valid_keys


def register(app: typer.Typer) -> None:  # noqa: C901
    @app.command("export-csv")
    @handle_user_errors
    def cmd_export_csv(
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
    ) -> None:
        """Экспортировать таблицу шлифов в формате CSV."""
        if output is None:
            quiet = True

        setup_logging(level=getattr(logging, log_level))
        logger = logging.getLogger("steinschliff")

        project_dir = PROJECT_ROOT
        schliffs_abs = os.path.join(project_dir, schliffs_dir)

        config = GeneratorConfig(
            schliffs_dir=Path(schliffs_abs),
            readme_file=Path(os.path.join(project_dir, "README_en.md")),
            readme_ru_file=Path(os.path.join(project_dir, "README.md")),
            sort_field=sort,
            translations_dir=Path(os.path.join(project_dir, "translations")),
        )
        try:
            generator = ReadmeGenerator(config)

            # В quiet-режиме подавляем rich/progress вывод при загрузке
            original_stdout: object | None = None
            if quiet:
                utils_module.console = Console(file=io.StringIO(), quiet=True)
                original_stdout = sys.stdout
                sys.stdout = io.StringIO()

            try:
                generator.load_structures()
                generator.load_service_metadata()
            finally:
                restore_stdout(original_stdout)

            try:
                selected_services = select_services(
                    services=generator.services,
                    service_metadata=generator.service_metadata,
                    service_filter=service,
                )
            except ValueError as e:
                raise SteinschliffUserError(str(e)) from e

            if condition:
                normalized_condition = normalize_condition_filter(condition)
                valid = set(get_valid_keys())
                if not normalized_condition or normalized_condition not in valid:
                    allowed = ", ".join(sorted(valid))
                    msg = f"Неизвестное условие '{condition}'. Допустимые: {allowed}"
                    raise SteinschliffUserError(msg)

                selected_services = filter_services_by_condition(
                    services=selected_services,
                    condition_key=normalized_condition,
                )
                if not selected_services:
                    console.print(Panel.fit(f"Не найдено структур с условием '{condition}'", border_style="yellow"))
                    raise typer.Exit(code=0)

            csv_content = export_structures_csv_string(
                services=selected_services,
                sort_key=generator._get_structure_sort_key,
            )

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
