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
from scripts.cli.common import PROJECT_ROOT, console, export_csv_content, normalize_condition_filter
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging


def register(app: typer.Typer) -> None:  # noqa: C901
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
    ) -> None:
        """Экспортировать таблицу шлифов в формате CSV."""
        if output is None:
            quiet = True

        setup_logging(level=getattr(logging, log_level))
        logger = logging.getLogger("steinschliff")

        project_dir = PROJECT_ROOT
        schliffs_abs = os.path.join(project_dir, schliffs_dir)

        config = {
            "schliffs_dir": schliffs_abs,
            "readme_file": "README_en.md",
            "readme_ru_file": "README.md",
            "sort_field": sort,
            "translations_dir": os.path.join(project_dir, "translations"),
        }
        try:
            if quiet:
                devnull_console = Console(file=io.StringIO(), quiet=True)
                utils_module.console = devnull_console

            generator = ReadmeGenerator(config)

            if quiet:
                prev_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    generator.load_structures()
                    generator.load_service_metadata()
                finally:
                    sys.stdout = prev_stdout
            else:
                generator.load_structures()
                generator.load_service_metadata()

            service_name_to_key: dict[str, str] = {}
            for key, meta in generator.service_metadata.items():
                visible_name = (meta.name or key).strip()
                service_name_to_key[visible_name.lower()] = key

            selected_services: dict[str, list] = dict(generator.services)

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

            if condition:
                normalized_condition = normalize_condition_filter(condition)
                if not normalized_condition:
                    console.print(
                        Panel.fit(
                            f"Неизвестное условие '{condition}'. "
                            "Допустимые: red, blue, violet, orange, green, yellow, pink, brown",
                            border_style="red",
                        )
                    )
                    raise typer.Exit(code=1)

                filtered_services: dict[str, list] = {}
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

            csv_content = export_csv_content(generator=generator, selected_services=selected_services)

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
