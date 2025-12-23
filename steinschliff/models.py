"""
Модели данных для Steinschliff.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Допустимые значения для condition из SnowCondition
DEFAULT_SNOW_CONDITIONS = ["red", "blue", "violet", "orange", "green", "yellow", "pink", "brown"]


def get_valid_snow_condition_keys() -> list[str]:
    """
    Возвращает список допустимых ключей для condition из файлов snow_conditions/*.yaml.

    Returns:
        Список строк с ключами: ['red', 'blue', 'violet', 'orange', 'green', 'yellow', 'pink', 'brown']
    """
    project_root = Path(__file__).resolve().parents[1]
    snow_conditions_dir = project_root / "snow_conditions"

    if not snow_conditions_dir.exists():
        # Возвращаем хардкодный список, если директория недоступна
        return DEFAULT_SNOW_CONDITIONS

    valid_keys = []
    for yaml_file in snow_conditions_dir.glob("*.yaml"):
        try:
            with yaml_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict) and "key" in data:
                    valid_keys.append(str(data["key"]))
        except (OSError, yaml.YAMLError):
            continue

    return sorted(valid_keys) if valid_keys else DEFAULT_SNOW_CONDITIONS


class TemperatureRange(BaseModel):
    """Диапазон температуры снега"""

    min: float
    max: float

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


class Service(BaseModel):
    """Модель сервиса по обработке лыж"""

    name: str | None = ""

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


class SchliffStructure(BaseModel):
    """Модель структуры"""

    name: str | int
    description: str | None
    description_ru: str | None = ""
    snow_type: list[str | int | None] | str | None = []
    temperature: list[TemperatureRange] | None = []
    condition: str | None = Field(
        default="",
        description=(
            "Условия снега из SnowCondition. Допустимые значения: red, blue, violet, "
            "orange, green, yellow, pink, brown, или пустая строка."
        ),
    )
    manufactory: str | None = ""
    service: Service | None = None
    author: str | None = ""
    country: str | None = ""
    tags: list[str | int | None] | None = []
    similars: list[str | int | None] | None = []
    features: list[str | int | None] | None = []  # Особенности структуры
    images: list[str] | None = None  # Путь к множественным изображениям шлифта

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: Any) -> str:
        """
        Валидирует, что condition является допустимым ключом из SnowCondition.

        Args:
            v: Значение для проверки

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если значение не является допустимым ключом SnowCondition
        """
        if v is None:
            return ""

        value = str(v).strip().lower()
        if not value:
            return ""

        valid_keys = get_valid_snow_condition_keys()
        if value not in valid_keys:
            valid_str = ", ".join(valid_keys)
            msg = f"condition must be one of valid SnowCondition keys: {valid_str}. Got: '{v}'"
            raise ValueError(msg)

        return value


class ContactInfo(BaseModel):
    """Модель контактной информации"""

    email: str | None = None
    phones: list[str] | None = None  # Массив телефонных номеров
    telegram: str | None = None
    address: str | None = None  # Адрес

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


class ServiceMetadata(BaseModel):
    """Модель метаданных сервиса обработки лыж"""

    name: str | None = ""
    description: str | None = ""
    description_ru: str | None = ""
    website_url: str | None = ""
    video_url: str | None = ""
    country: str | None = ""
    city: str | None = ""
    contact: ContactInfo | None = None

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


class StructureInfo(BaseModel):
    """Модель обработанной информации о структуре для вывода в README"""

    name: str
    description: str | None = ""
    description_ru: str | None = ""
    snow_type: str | None = ""
    temperature: list[dict[str, Any]] = Field(default_factory=list)
    condition: str | None = Field(
        default="",
        description=(
            "Условия снега из SnowCondition. Допустимые значения: red, blue, violet, "
            "orange, green, yellow, pink, brown, или пустая строка."
        ),
    )
    service: Service | None = None
    country: str | None = ""
    tags: list[str | int | None] = Field(default_factory=list)
    similars: list[str | int | None] = Field(default_factory=list)
    features: list[str | int | None] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    file_path: str

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


class SnowCondition(BaseModel):
    """Классификация снеговых условий (по цветам Skiwax)."""

    key: str  # канонический ключ: pink, yellow, orange, red, violet, blue, green, brown
    name: str
    name_ru: str | None = ""
    color: str | None = ""
    temperature: list[TemperatureRange] | None = None  # Диапазон температур
    snow_age: list[str] | None = []  # например: ["new"], ["old"], ["transformed"]
    humidity: list[str] | None = []  # например: ["saturated", "wet", "dry", "very_dry"]
    texture: list[str] | None = (
        []
    )  # например: ["powdery", "coarse", "icy", "sugary", "slushy", "glazing", "squeaky", "dirty"]
    description: str | None = ""
    description_ru: str | None = ""
    friction: str | None = ""
    friction_ru: str | None = ""
    synonyms: list[str] | None = []
    synonyms_ru: list[str] | None = []
    source_url: str | None = ""

    model_config = ConfigDict(extra="allow")  # Разрешаем доп. поля (например, any_temperature)
