"""
Модели данных для Steinschliff.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    snow_temperature: list[TemperatureRange] | None = []
    condition: str | None = ""
    manufactory: str | None = ""
    service: Service | None = None
    author: str | None = ""
    country: str | None = ""
    tags: list[str | int | None] | None = []
    similars: list[str | int | None] | None = []
    features: list[str | int | None] | None = []  # Особенности структуры
    images: list[str] | None = None  # Путь к множественным изображениям шлифта

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


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
    snow_temperature: list[dict[str, Any]] = Field(default_factory=list)
    service: Service | None = None
    country: str | None = ""
    tags: list[str | int | None] = Field(default_factory=list)
    similars: list[str | int | None] = Field(default_factory=list)
    features: list[str | int | None] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    file_path: str

    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля
