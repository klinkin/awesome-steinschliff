"""
Генератор README для Steinschliff.
"""

import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

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
        self.services: defaultdict[str, list[StructureInfo]] = defaultdict(list)
        self.name_to_path: dict[str, str] = {}
        self.service_metadata: dict[str, ServiceMetadata] = {}

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
        self.jinja_env.filters["format_image_link"] = format_image_link
        self.jinja_env.filters["format_list"] = format_list_for_display
        self.jinja_env.filters["format_similars"] = format_similars_with_links
        self.jinja_env.filters["format_temperature"] = format_temperature_range
        self.jinja_env.filters["format_features"] = format_features
        self.jinja_env.filters["relpath"] = lambda p, start: os.path.relpath(p, start)
        self.jinja_env.filters["phone_link"] = lambda phone: f"[{str(phone)}](tel:{str(phone)})"

    def load_structures(self) -> None:
        """Загружает структуры из YAML-файлов."""
        yaml_files = find_yaml_files(self.schliffs_dir)
        logger.info("Найдено %d YAML-файлов", len(yaml_files))

        self._process_yaml_files(yaml_files)

    def load_service_metadata(self) -> None:
        """Загружает метаданные для сервисов."""
        # Получаем список сервисов
        services = list(self.services.keys())

        # Загружаем метаданные - передаем корневую директорию schliffs
        self.service_metadata = read_service_metadata(self.schliffs_dir, services)

    def _process_yaml_files(self, yaml_files: list[str]) -> None:
        """
        Обрабатывает YAML-файлы для извлечения информации о структурах.
        Оптимизированная версия - обработка выполняется за один проход.

        Args:
            yaml_files: Список путей к YAML-файлам.
        """
        services: defaultdict[str, list[StructureInfo]] = defaultdict(list)
        name_to_path: dict[str, str] = {}
        processed_count = 0
        error_count = 0

        # Счетчики для статистики валидации
        valid_files = 0
        error_files = 0
        warning_files = 0

        # Один проход по всем файлам - одновременно создаем name_to_path и обрабатываем структуры
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

                # data может быть только dict из read_yaml_file для обычных файлов
                assert isinstance(data, dict)
                name = data.get("name", os.path.basename(file_path).replace(".yaml", ""))
                # Преобразуем имя в строку, чтобы обеспечить единый тип ключей
                name_str = str(name)
                name_to_path[name_str] = file_path
                valid_files += 1

                # Далее обрабатываем структуру и создаем StructureInfo
                # Определяем сервис
                service = os.path.dirname(file_path).replace(f"{self.schliffs_dir}/", "")
                if not service:
                    service = "main"

                # Обрабатываем snow_type для форматированного вывода
                formatted_snow_type = format_snow_types(data.get("snow_type", []))

                # Получаем значение service и создаем объект Service
                service_data = data.get("service", {})
                if isinstance(service_data, dict):
                    service_obj = Service(name=service_data.get("name", ""))
                else:
                    service_obj = Service(name=service_data or "")

                # Сохраняем структуру в соответствующий сервис
                structure_info = StructureInfo(
                    name=name_str,
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
                )

                services[service].append(structure_info)
                processed_count += 1
            except (OSError, ValueError, TypeError) as e:
                error_count += 1
                error_files += 1
                logger.error("Непредвиденная ошибка при обработке %s: %s", file_path, e)

        logger.info("Успешно обработано %d файлов с %d ошибками", processed_count, error_count)
        self.services = services
        self.name_to_path = name_to_path

        # Выводим статистику валидации
        print_validation_summary(valid_files, error_files, warning_files)

    def get_path_by_name(self, name: str) -> str | None:
        """
        Возвращает путь к файлу структуры по её имени.

        Args:
            name: Имя структуры

        Returns:
            Путь к файлу или None, если структура не найдена
        """
        return self.name_to_path.get(str(name))

    def _get_structure_sort_key(self, structure: StructureInfo) -> Any:
        """
        Возвращает ключ для сортировки структуры в зависимости от выбранного поля сортировки.

        Args:
            structure: Информация о структуре

        Returns:
            Ключ для сортировки
        """
        if self.sort_field == "temperature":
            # Сортировка по температуре (сначала самые теплые)
            if (
                structure.snow_temperature
                and isinstance(structure.snow_temperature, list)
                and structure.snow_temperature[0]
            ):
                temp_range = structure.snow_temperature[0]
                max_temp = temp_range.get("max")
                if max_temp is not None:
                    try:
                        return -float(max_temp)  # Негативное значение для сортировки по убыванию
                    except (ValueError, TypeError):
                        pass
            # Структуры без температуры отправляем в конец сортировки
            return float("inf")
        else:
            # Сортировка по имени или другому полю
            return getattr(structure, self.sort_field, "") or ""

    def _prepare_countries_data(self) -> dict[str, Any]:
        """Подготавливает иерархические данные о странах, сервисах и структурах."""
        countries: dict[str, dict[str, Any]] = {}

        # Сначала группируем сервисы по странам
        for service_name, structures in self.services.items():
            # Определяем страну для сервиса из метаданных
            country = "Other"
            if service_name in self.service_metadata:
                service_meta = self.service_metadata[service_name]
                if service_meta.country:
                    country = service_meta.country

            # Извлекаем метаданные сервиса, если они есть (отдельно от переменной выше)
            service_meta_opt: ServiceMetadata | None = self.service_metadata.get(service_name)

            # Если страны еще нет в словаре, создаем её
            if country not in countries:
                countries[country] = {"services": {}}

            # Добавляем сервис в страну
            service_data: dict[str, Any] = {
                "name": service_name,
                "structures": structures,
            }

            if service_meta_opt:
                service_data.update(
                    {
                        "title": service_meta_opt.name or service_name.capitalize(),
                        "city": service_meta_opt.city or "",
                        "description": service_meta_opt.description or "",
                        "description_ru": service_meta_opt.description_ru or "",
                        "website_url": service_meta_opt.website_url or "",
                        "video_url": service_meta_opt.video_url or "",
                        "contact": service_meta_opt.contact or {},
                    }
                )
            else:
                service_data.update(
                    {
                        "title": service_name.capitalize(),
                        "city": "",
                        "description": "",
                        "description_ru": "",
                        "website_url": "",
                        "video_url": "",
                        "contact": {},
                    }
                )

            countries[country]["services"][service_name] = service_data

        # Определяем порядок стран
        ordered_countries: list[str] = []

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

        self.jinja_env.filters["format_similars"] = lambda similars, output_dir: format_similars_with_links(
            similars, self, output_dir
        )

        # Добавляем функцию для сортировки по температуре
        if self.sort_field == "temperature":
            # Подготавливаем отсортированные структуры для каждого сервиса
            for country in countries_data["countries"].values():
                for service_name, service_data in country["services"].items():
                    structures = service_data["structures"]
                    # Сортируем структуры по максимальной температуре (сначала теплые)
                    service_data["structures"] = sorted(structures, key=self._get_structure_sort_key)

        # Генерируем README для каждого языка
        locales = {
            "en": {"output_file": self.readme_file, "description_field": "description"},
            "ru": {"output_file": self.readme_ru_file, "description_field": "description_ru"},
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
            # Устанавливаем переводы для Jinja2 через globals, чтобы избежать проблем с типами
            self.jinja_env.add_extension("jinja2.ext.i18n")
            self.jinja_env.globals.update(
                _=translations.gettext, gettext=translations.gettext, ngettext=translations.ngettext
            )

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

            logger.info("README для языка %s успешно сгенерирован в %s", locale.upper(), os.path.abspath(output_file))

    def run(self) -> None:
        """Запускает процесс генерации README."""
        self.load_structures()
        self.load_service_metadata()
        self.generate()


def export_json(services: dict[str, list["StructureInfo"]], out_path: str):
    """Экспортирует данные о структурах в JSON-формат для Astro-сайта."""
    flat = []
    for service, items in services.items():
        for s in items:
            tr = s.snow_temperature[0] if s.snow_temperature else None
            flat.append(
                {
                    "name": s.name,
                    "service": (s.service.name if s.service else service) or service,
                    "country": s.country or "",
                    "snow_type": (s.snow_type or "").strip(),
                    "temp_min": tr.get("min") if tr else None,
                    "temp_max": tr.get("max") if tr else None,
                    "tags": [t for t in (s.tags or []) if t],
                    "similars": [x for x in (s.similars or []) if x],
                    "features": [x for x in (s.features or []) if x],
                    "images": s.images or [],
                    "file_path": s.file_path,
                }
            )
    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=2)
