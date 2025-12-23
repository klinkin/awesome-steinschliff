from __future__ import annotations

import logging
import os
from typing import Literal

import typer
from rich.panel import Panel
from rich.table import Table

from scripts.cli.common import PROJECT_ROOT, build_generator, console
from steinschliff.export.json import export_structures_json
from steinschliff.logging import setup_logging


def register(app: typer.Typer) -> None:
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
    ) -> None:
        """Только экспорт JSON-данных для веб-приложения."""
        setup_logging(level=getattr(logging, log_level))
        logger = logging.getLogger("steinschliff")

        project_dir = PROJECT_ROOT
        schliffs_abs = os.path.join(project_dir, schliffs_dir)

        _, generator, _ = build_generator(
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
            export_structures_json(services=generator.services, out_path=out_path)

            summary = Table.grid(padding=(0, 1))
            summary.add_row("[bold]JSON[/]:", f"[cyan]{out_path}[/]")
            console.print(Panel.fit(summary, title="JSON экспортирован", border_style="blue"))
        except Exception as err:
            logger.exception("Ошибка при экспорте JSON")
            raise typer.Exit(code=1) from err
