from __future__ import annotations

import logging
from typing import Literal

import typer
from rich.panel import Panel

from steinschliff.catalog import filter_services_by_condition, select_services
from steinschliff.cli.common import PROJECT_ROOT, console, normalize_condition_filter, render_table
from steinschliff.cli.error_handler import handle_user_errors
from steinschliff.config import GeneratorConfig
from steinschliff.exceptions import SteinschliffUserError
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging
from steinschliff.snow_conditions import get_valid_keys


def register(app: typer.Typer) -> None:
    @app.command("list")
    @handle_user_errors
    def cmd_list(
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
        schliffs_abs = (project_dir / schliffs_dir).resolve()

        config = GeneratorConfig(
            schliffs_dir=schliffs_abs,
            readme_file=(project_dir / "README_en.md").resolve(),
            readme_ru_file=(project_dir / "README.md").resolve(),
            sort_field=sort,
            translations_dir=(project_dir / "translations").resolve(),
        )
        try:
            generator = ReadmeGenerator(config)
            generator.load_structures()
            generator.load_service_metadata()

            try:
                selected_services = select_services(
                    services=generator.services,
                    service_metadata=generator.service_metadata,
                    service_filter=service,
                )
            except ValueError as e:
                raise SteinschliffUserError(str(e)) from e

            normalized_condition = None
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
