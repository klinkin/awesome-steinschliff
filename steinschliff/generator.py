"""
Генератор README для Steinschliff.
"""

import logging
import os
import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader
from jinja2.ext import i18n

from .formatters import (
    format_features,
    format_image_link,
    format_list_for_display,
    format_similars_with_links,
    format_snow_types,
    format_temperature_range,
)
from .i18n import load_translations
from .models import Service, ServiceMetadata, StructureInfo
from .utils import (
    find_yaml_files,
    print_validation_summary,
    read_service_metadata,
    read_yaml_file,
)

logger = logging.getLogger("steinschliff.generator")


class ReadmeGenerator:
    """Класс для генерации README из YAML-файлов структур."""

    def __init__(self, config: dict) -> None:
        """Инициализирует генератор.

        Args:
            config: Словарь с конфигурацией генератора.
        """
        self.schliffs_dir = config["schliffs_dir"]
        self.readme_file = config["readme_file"]
        self.readme_ru_file = config["readme_ru_file"]
        self.sort_field = config.get("sort_field", "name")

        # Инициализируем пустые структуры данных
        self.services = defaultdict(list)
        self.name_to_path = {}
        self.service_metadata = {}

        # Устанавливаем окружение Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
            extensions=[i18n],
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Добавляем функцию getattr в глобальный контекст Jinja2
        self.jinja_env.globals["getattr"] = getattr

        # Регистрируем фильтры для шаблонов
        self.jinja_env.filters["format_image"] = format_image_link
        self.jinja_env.filters["format_list"] = format_list_for_display
        self.jinja_env.filters["format_similars"] = format_similars_with_links
        self.jinja_env.filters["format_temperature"] = format_temperature_range
        self.jinja_env.filters["format_features"] = format_features
        self.jinja_env.filters["relpath"] = lambda p, start: os.path.relpath(p, start)
        self.jinja_env.filters["phone_link"] = lambda phone: f"[{str(phone)}](tel:{str(phone)})"

    def load_structures(self) -> None:
        """Загружает структуры из YAML-файлов."""
        yaml_files = find_yaml_files(self.schliffs_dir)
        logger.info(f"Найдено {len(yaml_files)} YAML-файлов")

        self._process_yaml_files(yaml_files)

    def load_service_metadata(self) -> None:
        """Загружает метаданные для сервисов."""
        # Получаем список сервисов
        services = list(self.services.keys())

        # Загружаем метаданные - передаем корневую директорию schliffs
        self.service_metadata = read_service_metadata(self.schliffs_dir, services)

    def _process_yaml_files(self, yaml_files: List[str]) -> None:
        """
        Обрабатывает YAML-файлы для извлечения информации о структурах.

        Args:
            yaml_files: Список путей к YAML-файлам.
        """
        services = defaultdict(list)
        name_to_path = {}
        processed_count = 0
        error_count = 0

        # Счетчики для статистики валидации
        valid_files = 0
        error_files = 0
        warning_files = 0

        # Первый проход - создаем отображение имен на пути
        for file_path in yaml_files:
            try:
                # Пропускаем файлы _meta.yaml
                if os.path.basename(file_path) == "_meta.yaml":
                    continue

                data = read_yaml_file(file_path)
                if not data:
                    error_count += 1
                    error_files += 1
                    continue

                name = data.get("name", os.path.basename(file_path).replace(".yaml", ""))
                # Преобразуем имя в строку, чтобы обеспечить единый тип ключей
                name_to_path[str(name)] = file_path
                valid_files += 1
            except Exception as e:
                error_count += 1
                error_files += 1
                logger.error(f"Непредвиденная ошибка при обработке {file_path}: {e}")

        # Второй проход - обрабатываем структуры с полным отображением
        for file_path in yaml_files:
            try:
                # Пропускаем файлы _meta.yaml
                if os.path.basename(file_path) == "_meta.yaml":
                    continue

                data = read_yaml_file(file_path)
                if not data:
                    continue

                # Определяем сервис
                service = os.path.dirname(file_path).replace(f"{self.schliffs_dir}/", "")
                if not service:
                    service = "main"

                # Создаем информацию о структуре используя StructureInfo
                name = data.get("name", os.path.basename(file_path).replace(".yaml", ""))

                # Обрабатываем snow_type для форматированного вывода
                formatted_snow_type = format_snow_types(data.get("snow_type", []))

                # Получаем значение service и создаем объект Service
                service_data = data.get("service", {})
                if isinstance(service_data, dict):
                    service_obj = Service(name=service_data.get("name", ""))
                else:
                    service_obj = Service(name=service_data or "")

                # Создаем объект StructureInfo
                structure_info = StructureInfo(
                    name=str(name),  # Конвертируем name в строку
                    description=data.get("description", ""),
                    description_ru=data.get("description_ru", ""),
                    snow_type=formatted_snow_type,
                    snow_temperature=data.get("snow_temperature", []),
                    service=service_obj,
                    country=data.get("country", ""),
                    tags=data.get("tags", []),
                    similars=data.get("similars", []),
                    features=data.get("features", []),
                    images=data.get("images", []),
                    file_path=file_path,
                    name_to_path={},  # Будет заполнено позже
                )

                services[service].append(structure_info)
                processed_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Непредвиденная ошибка при обработке {file_path}: {e}")

        # Добавляем ссылку на name_to_path для каждой структуры
        for service_name, service_structures in services.items():
            for i, structure in enumerate(service_structures):
                # Обновляем поле name_to_path для каждой структуры
                # Создаем копию структуры с обновленным полем
                updated_structure = structure.model_copy(update={"name_to_path": name_to_path})
                services[service_name][i] = updated_structure

        logger.info(f"Успешно обработано {processed_count} файлов с {error_count} ошибками")
        self.services = services
        self.name_to_path = name_to_path

        # Выводим статистику валидации
        print_validation_summary(valid_files, error_files, warning_files)

    def _prepare_countries_data(self) -> Dict[str, Any]:
        """Подготавливает иерархические данные о странах, сервисах и структурах."""
        countries = {}

        # Сначала группируем сервисы по странам
        for service_name, structures in self.services.items():
            # Определяем страну для сервиса из метаданных
            country = "Other"
            if service_name in self.service_metadata:
                service_meta = self.service_metadata[service_name]
                if service_meta.get("country"):
                    country = service_meta.get("country")

            # Извлекаем метаданные сервиса, если они есть
            service_meta = self.service_metadata.get(service_name, {})

            # Если страны еще нет в словаре, создаем её
            if country not in countries:
                countries[country] = {"services": {}}

            # Добавляем сервис в страну
            countries[country]["services"][service_name] = {
                "name": service_name,
                "title": service_meta.get("name", service_name.capitalize()),
                "city": service_meta.get("city", ""),
                "description": service_meta.get("description", ""),
                "description_ru": service_meta.get("description_ru", ""),
                "website_url": service_meta.get("website_url", ""),
                "video_url": service_meta.get("video_url", ""),
                "contact": service_meta.get("contact", {}),
                "structures": structures,
            }

        # Определяем порядок стран
        ordered_countries = []

        # Сначала добавляем Россию, если она есть
        if "Россия" in countries:
            ordered_countries.append("Россия")

        # Затем добавляем остальные страны в алфавитном порядке, кроме Other
        for country in sorted(countries.keys()):
            if country != "Россия" and country != "Other":
                ordered_countries.append(country)

        # И в конце добавляем Other, если там есть сервисы
        if "Other" in countries and countries["Other"]["services"]:
            ordered_countries.append("Other")

        return {"countries": countries, "ordered_countries": ordered_countries}

    # Примечание по шаблонам:
    # Шаблоны были разбиты на модульные компоненты для улучшения поддерживаемости:
    # - base.jinja2 - базовый шаблон с общей структурой
    # - header.jinja2 - заголовок в зависимости от языка
    # - toc.jinja2 - оглавление (содержание)
    # - service.jinja2 - шаблон для отдельного сервиса
    # - table.jinja2 - таблица структур
    # Все эти компоненты подключаются из основного шаблона readme.jinja2,
    # который использует механизмы Jinja2 extends и include.

    def generate(self) -> None:
        """Генерирует README файлы на основе загруженных данных."""
        if not self.services:
            logger.warning("Нет данных о структурах для генерации README")
            return

        countries_data = self._prepare_countries_data()

        # Компилируем шаблон
        template = self.jinja_env.get_template("readme.jinja2")

        # Генерируем README для каждого языка
        locales = {
            "en": {
                "output_file": self.readme_file,
                "description_field": "description"
            },
            "ru": {
                "output_file": self.readme_ru_file,
                "description_field": "description_ru"
            },
        }

        for locale, locale_data in locales.items():
            output_file = locale_data["output_file"]
            description_field = locale_data["description_field"]

            # Получаем выходную директорию (для вычисления относительных путей)
            output_dir = os.path.dirname(os.path.abspath(output_file))
            if not output_dir:
                output_dir = os.getcwd()

            # Загружаем переводы для текущей локали
            translations = load_translations(locale)

            # Устанавливаем переводы для Jinja2
            # Используем новый стиль gettext для лучшей работы с форматированием строк
            self.jinja_env.install_gettext_translations(translations, newstyle=True)

            # Подготавливаем данные для шаблона
            template_data = {
                "countries": countries_data["countries"],
                "ordered_countries": countries_data["ordered_countries"],
                "sort_by": self.sort_field,
                "output_dir": output_dir,
                "language": locale,
                "description_field": description_field,
            }

            # Рендерим шаблон
            rendered_content = template.render(**template_data)

            # Записываем результат в файл
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered_content)

            logger.info(f"README для языка {locale.upper()} успешно сгенерирован в {os.path.abspath(output_file)}")

    def run(self) -> None:
        """Запускает процесс генерации README."""
        self.load_structures()
        self.load_service_metadata()
        self.generate()
