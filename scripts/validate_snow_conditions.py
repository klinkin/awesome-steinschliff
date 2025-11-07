#!/usr/bin/env python3
"""
Скрипт валидации YAML файлов snow_conditions/*.yaml с использованием SnowCondition.model_validate.

Проверяет все файлы в директории snow_conditions/ на соответствие модели SnowCondition.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))

import argparse  # noqa: E402
import logging  # noqa: E402
from typing import Any  # noqa: E402

import yaml  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from steinschliff.models import SnowCondition  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
console = Console()


def load_yaml_file(file_path: Path) -> dict[str, Any] | None:
    """Загружает YAML файл."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                data = {}
            if not isinstance(data, dict):
                logger.error("Файл %s должен содержать YAML-объект (mapping)", file_path)
                return None
            return data
    except yaml.YAMLError as e:
        logger.error("Ошибка разбора YAML в %s: %s", file_path, e)
        return None
    except OSError as e:
        logger.error("Ошибка чтения файла %s: %s", file_path, e)
        return None


def validate_snow_condition_file(file_path: Path) -> tuple[bool, SnowCondition | None, ValidationError | None]:
    """
    Валидирует файл snow condition.

    Returns:
        (is_valid, snow_condition_object, validation_error)
    """
    data = load_yaml_file(file_path)
    if data is None:
        return False, None, None

    try:
        condition = SnowCondition.model_validate(data)
        return True, condition, None
    except ValidationError as e:
        return False, None, e


def format_validation_error(err: ValidationError, file_path: Path) -> str:
    """Форматирует ошибку валидации в читаемый вид."""
    errors = err.errors()
    report = [f"[bold red]ОШИБКИ ВАЛИДАЦИИ В ФАЙЛЕ: {file_path}[/]"]
    report.append("=" * 60)

    for i, error in enumerate(errors, 1):
        loc = " -> ".join([str(loc_part) for loc_part in error.get("loc", [])])
        error_type = error.get("type", "")
        msg = error.get("msg", "")

        report.append(f"\n[bold]Ошибка #{i}:[/]")
        report.append(f"  [cyan]Поле:[/]  [bold]{loc}[/]")
        report.append(f"  [cyan]Тип:[/]   [magenta]{error_type}[/]")
        report.append(f"  [cyan]Текст:[/] [red]{msg}[/]")

    return "\n".join(report)


def print_validation_errors(err: ValidationError, file_path: Path) -> None:
    """Печатает ошибки валидации в виде таблицы Rich."""
    errors = err.errors()

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Поле")
    table.add_column("Тип")
    table.add_column("Текст")

    for error in errors:
        loc = " -> ".join([str(loc_part) for loc_part in error.get("loc", [])])
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        table.add_row(f"[bold]{loc}[/]", f"[magenta]{error_type}[/]", f"[red]{msg}[/]")

    console.print(Panel.fit(table, title=f"Ошибки валидации в файле: {file_path}", border_style="red"))


def print_validation_summary(valid_files: int, error_files: int, total: int) -> None:
    """Выводит сводку по результатам валидации."""
    valid_percent = (valid_files / total * 100) if total else 0
    error_percent = (error_files / total * 100) if total else 0

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Статус")
    table.add_column("Кол-во", justify="right")
    table.add_column("Доля", justify="right")

    table.add_row("[green]✓ Успешно[/]", str(valid_files), f"{valid_percent:.1f}%")
    table.add_row("[red]✗ Ошибки[/]", str(error_files), f"{error_percent:.1f}%")

    console.print(Panel.fit(table, title="Результаты валидации Snow Conditions", border_style="cyan"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Валидация YAML файлов snow_conditions/*.yaml")
    parser.add_argument(
        "--dir",
        type=str,
        default="snow_conditions",
        help="Директория с YAML файлами snow conditions (по умолчанию: snow_conditions)",
    )
    parser.add_argument("--verbose", action="store_true", help="Подробный вывод")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    base_dir = Path(args.dir)
    if not base_dir.exists() or not base_dir.is_dir():
        logger.error("Директория %s не существует или не является директорией", base_dir)
        return 1

    yaml_files = sorted(base_dir.glob("*.yaml"))
    if not yaml_files:
        logger.warning("Не найдено YAML файлов в директории %s", base_dir)
        return 0

    logger.info("Найдено %d YAML файлов для валидации", len(yaml_files))

    valid_files = 0
    error_files = 0
    error_details: list[tuple[Path, ValidationError]] = []

    for file_path in yaml_files:
        is_valid, condition, error = validate_snow_condition_file(file_path)

        if is_valid:
            valid_files += 1
            if args.verbose:
                console.print(f"[green]✓[/] {file_path.name}: валиден")
                if condition:
                    console.print(f"   Key: {condition.key}, Name: {condition.name}")
        else:
            error_files += 1
            if error:
                error_details.append((file_path, error))
                print_validation_errors(error, file_path)
            else:
                logger.error("Не удалось загрузить файл: %s", file_path)

    print_validation_summary(valid_files, error_files, len(yaml_files))

    if error_files > 0:
        logger.error("Обнаружено %d файлов с ошибками валидации", error_files)
        return 1

    logger.info("Все файлы успешно прошли валидацию!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
