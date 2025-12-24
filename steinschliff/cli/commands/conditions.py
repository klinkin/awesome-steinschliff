from __future__ import annotations

import logging
from typing import Literal

import typer
from rich.table import Table

from steinschliff.cli.common import PROJECT_ROOT, console
from steinschliff.config import GeneratorConfig
from steinschliff.formatters import format_temperature_range
from steinschliff.generator import ReadmeGenerator
from steinschliff.logging import setup_logging
from steinschliff.snow_conditions import get_condition_info, get_valid_keys


def register(app: typer.Typer) -> None:
    @app.command("conditions")
    def cmd_conditions(
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
    ) -> None:
        """Показать статистику по условиям снега (snow conditions)."""
        setup_logging(level=getattr(logging, log_level))
        logger = logging.getLogger("steinschliff")

        project_dir = PROJECT_ROOT
        schliffs_abs = (project_dir / schliffs_dir).resolve()

        config = GeneratorConfig(
            schliffs_dir=schliffs_abs,
            readme_file=(project_dir / "README_en.md").resolve(),
            readme_ru_file=(project_dir / "README.md").resolve(),
            sort_field="name",
            translations_dir=(project_dir / "translations").resolve(),
        )

        try:
            generator = ReadmeGenerator(config)
            generator.load_structures()

            condition_counts: dict[str, int] = {}
            total_structures = 0

            for service_structures in generator.services.values():
                for structure in service_structures:
                    total_structures += 1
                    if structure.condition:
                        key = structure.condition.strip().lower()
                        condition_counts[key] = condition_counts.get(key, 0) + 1

            conditions_info: dict[str, dict[str, object]] = {}
            for key in get_valid_keys():
                info = get_condition_info(key) or {}
                conditions_info[key] = {
                    "name_ru": info.get("name_ru", key),
                    "color": info.get("color", ""),
                    "temperature": info.get("temperature"),
                }

            # Маппинг цветов на emoji (как было в исходном CLI)
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

            sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)

            for condition_key, count in sorted_conditions:
                info = conditions_info.get(condition_key, {})
                emoji = color_emoji.get(condition_key, "⚪")
                name_ru = str(info.get("name_ru", condition_key.capitalize()))

                temp = info.get("temperature")
                temp_str = (
                    format_temperature_range(temp) if temp and isinstance(temp, list) and len(temp) > 0 else "любая"
                )

                percentage = (count / total_structures * 100) if total_structures > 0 else 0

                table.add_row(
                    condition_key.upper(),
                    emoji,
                    name_ru,
                    temp_str,
                    str(count),
                    f"{percentage:.1f}%",
                )

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

            if total_structures > 0:
                empty_conditions = total_structures - sum(condition_counts.values())
                if empty_conditions > 0:
                    console.print(f"[yellow]⚠️  Структур без condition: {empty_conditions}[/yellow]")
                else:
                    console.print("[green]✅ Все структуры имеют валидные значения condition![/green]")

        except Exception as err:
            logger.exception("Ошибка при получении статистики")
            raise typer.Exit(code=1) from err
