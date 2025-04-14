"""
Модели данных для Steinschliff.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TemperatureRange(BaseModel):
    """Диапазон температуры снега"""

    min: float
    max: float


class Service(BaseModel):
    """Модель сервиса по обработке лыж"""

    name: Optional[str] = ""

    class Config:
        """Конфигурация модели Pydantic"""

        extra = "allow"  # Разрешаем дополнительные поля


class SchliffStructure(BaseModel):
    """Модель структуры"""

    name: Union[str, int]
    description: Union[str, None]
    description_ru: Optional[str] = ""
    snow_type: Union[List[Union[str, int, None]], str, None] = []
    snow_temperature: Optional[List[TemperatureRange]] = []
    condition: Optional[str] = ""
    manufactory: Optional[str] = ""
    service: Optional[Service] = None
    author: Optional[str] = ""
    country: Optional[str] = ""
    tags: Optional[List[Union[str, int, None]]] = []
    similars: Optional[List[Union[str, int, None]]] = []
    features: Optional[List[Union[str, int, None]]] = []  # Особенности структуры
    images: Optional[List[str]] = None  # Путь к множественным изображениям шлифта

    class Config:
        """Конфигурация модели Pydantic"""

        extra = "allow"  # Разрешаем дополнительные поля


class ContactInfo(BaseModel):
    """Модель контактной информации"""

    email: Optional[str] = None
    phones: Optional[List[str]] = None  # Массив телефонных номеров
    telegram: Optional[str] = None
    address: Optional[str] = None  # Адрес

    class Config:
        """Конфигурация модели Pydantic"""

        extra = "allow"  # Разрешаем дополнительные поля


class ServiceMetadata(BaseModel):
    """Модель метаданных сервиса обработки лыж"""

    name: Optional[str] = ""
    description: Optional[str] = ""
    description_ru: Optional[str] = ""
    website_url: Optional[str] = ""
    video_url: Optional[str] = ""
    country: Optional[str] = ""
    city: Optional[str] = ""
    contact: Optional[ContactInfo] = None

    class Config:
        """Конфигурация модели Pydantic"""

        extra = "allow"  # Разрешаем дополнительные поля


class StructureInfo(BaseModel):
    """Модель обработанной информации о структуре для вывода в README"""

    name: str
    description: Optional[str] = ""
    description_ru: Optional[str] = ""
    snow_type: Optional[str] = ""
    snow_temperature: List[Dict[str, Any]] = Field(default_factory=list)
    service: Optional[Service] = None
    country: Optional[str] = ""
    tags: List[Union[str, int, None]] = Field(default_factory=list)
    similars: List[Union[str, int, None]] = Field(default_factory=list)
    features: List[Union[str, int, None]] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    file_path: str
    name_to_path: Dict[str, str] = Field(default_factory=dict)

    class Config:
        """Конфигурация модели Pydantic"""

        extra = "allow"  # Разрешаем дополнительные поля
