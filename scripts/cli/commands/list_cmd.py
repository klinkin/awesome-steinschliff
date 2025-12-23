from __future__ import annotations

import logging
import os
from typing import Literal

import typer
from rich.panel import Panel

from scripts.cli.common import PROJECT_ROOT, console, normalize_condition_filter, render_table
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging


def register(app: typer.Typer) -> None:  # noqa: C901
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
    ) -> None:
        """Показать таблицу шлифов. Можно отфильтровать по конкретному производителю и условиям снега."""
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
            generator = ReadmeGenerator(config)
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

            normalized_condition = None
            if condition:
                normalized_condition = normalize_condition_filter(condition)
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

            table = render_table(
                generator=generator,
                selected_services=selected_services,
                filter_service=service,
                filter_condition=normalized_condition if condition else None,
            )
            console.print(table)
        except Exception as err:
            logger.exception("Ошибка при построении списка")
            raise typer.Exit(code=1) from err
