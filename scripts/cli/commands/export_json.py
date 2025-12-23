from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

import typer
from rich.panel import Panel
from rich.table import Table

from scripts.cli.common import PROJECT_ROOT, console
from scripts.cli.error_handler import handle_user_errors
from steinschliff.config import GeneratorConfig
from steinschliff.export.json import export_structures_json
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging


def register(app: typer.Typer) -> None:
    @app.command("export-json")
    @handle_user_errors
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

        cfg = GeneratorConfig(
            schliffs_dir=Path(schliffs_abs),
            readme_file=Path(os.path.join(project_dir, "README_en.md")),
            readme_ru_file=Path(os.path.join(project_dir, "README.md")),
            sort_field=sort,
            translations_dir=Path(os.path.join(project_dir, "translations")),
        )
        try:
            generator = ReadmeGenerator(cfg)
            generator.load_structures()
            generator.load_service_metadata()
            export_structures_json(services=generator.services, out_path=out_path)

            summary = Table.grid(padding=(0, 1))
            summary.add_row("[bold]JSON[/]:", f"[cyan]{out_path}[/]")
            console.print(Panel.fit(summary, title="JSON экспортирован", border_style="blue"))
        except Exception as err:
            logger.exception("Ошибка при экспорте JSON")
            raise typer.Exit(code=1) from err
