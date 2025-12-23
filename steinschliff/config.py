from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

SortField = Literal["name", "rating", "country", "temperature"]


class GeneratorConfig(BaseModel):
    """Конфигурация ReadmeGenerator.

    Делаем контракт явным, чтобы:
    - избежать неявных KeyError по словарю
    - держать типы и дефолты в одном месте
    - упростить использование в CLI/тестах
    """

    schliffs_dir: Path
    readme_file: Path
    readme_ru_file: Path
    sort_field: SortField = "name"
    translations_dir: Path | None = None

    model_config = ConfigDict(frozen=True)

    def as_dict(self) -> dict[str, str | SortField]:
        """Совместимость со старым API `ReadmeGenerator(config: dict)`."""
        data: dict[str, str | SortField] = {
            "schliffs_dir": str(self.schliffs_dir),
            "readme_file": str(self.readme_file),
            "readme_ru_file": str(self.readme_ru_file),
            "sort_field": self.sort_field,
        }
        if self.translations_dir is not None:
            data["translations_dir"] = str(self.translations_dir)
        return data
