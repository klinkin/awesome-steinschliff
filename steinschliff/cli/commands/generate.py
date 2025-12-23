from __future__ import annotations

from typing import Literal

import typer

from steinschliff.cli.common import run_generate


def register(app: typer.Typer) -> None:
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
    ) -> None:
        """Сгенерировать README (EN и RU) и экспортировать JSON."""
        run_generate(
            schliffs_dir=schliffs_dir,
            output=output,
            output_ru=output_ru,
            sort=sort,
            translations_dir=translations_dir,
            log_level=log_level,
            create_translations=create_translations,
        )
