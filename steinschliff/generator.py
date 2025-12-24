"""Генератор README для Steinschliff.

Основная роль этого модуля — собрать зависимости (Jinja2, i18n, форматтеры, I/O)
и “оркестровать” pipeline генерации.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from jinja2.ext import i18n

from .config import GeneratorConfig
from .formatters import (
    format_features,
    format_image_link,
    format_list_for_display,
    format_similars_with_links,
    format_temperature_range,
    url_encode_path,
)
from .i18n import load_translations
from .io import read_service_metadata
from .models import ServiceMetadata, StructureInfo
from .paths import relpath, templates_dir
from .pipeline.readme import (
    build_template_data,
    discover_yaml_files,
    load_structures_from_yaml_files,
    prepare_countries_data,
    sort_countries_data_in_place,
)
from .ui.rich import print_kv_panel, print_validation_summary

logger = logging.getLogger("steinschliff.generator")


class ReadmeGenerator:
    """Генератор README из YAML-файлов структур.

    Генерация состоит из шагов:
    - load+validate: чтение YAML структур
    - load: чтение метаданных сервисов
    - transform: группировка по странам/сервисам, сортировка
    - render: рендер Jinja2-шаблона в README (ru/en)
    """

    def __init__(self, config: GeneratorConfig) -> None:
        """Создать генератор с заданной конфигурацией.

        Args:
            config: Конфигурация генератора (пути, sort_field и пр.).
        """
        self.schliffs_dir = str(config.schliffs_dir)
        self.readme_file = str(config.readme_file)
        self.readme_ru_file = str(config.readme_ru_file)
        self.sort_field = str(config.sort_field or "name")

        # Инициализируем пустые структуры данных
        self.services: defaultdict[str, list[StructureInfo]] = defaultdict(list)
        self.name_to_path: dict[str, str] = {}
        self.service_metadata: dict[str, ServiceMetadata] = {}

        # Устанавливаем окружение Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir())),
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
        self.jinja_env.filters["relpath"] = lambda p, start: str(relpath(p, start))
        self.jinja_env.filters["phone_link"] = lambda phone: f"[{phone!s}](tel:{phone!s})"
        self.jinja_env.filters["urlencode"] = url_encode_path

    def load_structures(self) -> None:
        """Загрузить структуры из YAML-файлов.

        Заполняет:
            - `self.services`
            - `self.name_to_path`

        Также печатает краткую сводку в консоль (UI слой).
        """
        yaml_files = discover_yaml_files(schliffs_dir=Path(self.schliffs_dir))
        print_kv_panel("Поиск YAML-файлов", [("Найдено", str(len(yaml_files)))])

        # Прогресс оставляем в генераторе (UI слой), а загрузку/валидацию — в pipeline.
        loaded = load_structures_from_yaml_files(yaml_files=yaml_files, schliffs_dir=Path(self.schliffs_dir))
        self.services = defaultdict(list, loaded.services)
        self.name_to_path = loaded.name_to_path

        print_kv_panel(
            "Итоги обработки YAML",
            [
                ("Успешно обработано", str(loaded.stats.processed_structures)),
                ("Ошибок", str(loaded.stats.error_files)),
            ],
            border_style="green" if loaded.stats.error_files == 0 else "red",
        )
        print_validation_summary(loaded.stats.valid_files, loaded.stats.error_files, loaded.stats.warning_files)

    def load_service_metadata(self) -> None:
        """Загрузить метаданные сервисов из `_meta.yaml`.

        Заполняет:
            - `self.service_metadata`
        """
        # Получаем список сервисов
        services = list(self.services.keys())

        # Загружаем метаданные - передаем корневую директорию schliffs
        self.service_metadata = read_service_metadata(self.schliffs_dir, services)

    # NOTE: шаг load+validate вынесен в steinschliff.pipeline.readme

    def get_path_by_name(self, name: str) -> str | None:
        """Получить путь к файлу структуры по её имени.

        Args:
            name: Имя структуры (как в поле `name`).

        Returns:
            Путь к YAML-файлу структуры или `None`, если структура не найдена.
        """
        return self.name_to_path.get(str(name))

    def _get_structure_sort_key(self, structure: StructureInfo) -> Any:
        """Вернуть ключ сортировки для структуры.

        Note:
            Метод оставлен для обратной совместимости с кодом/тестами, но “источник истины”
            для сортировки теперь находится в `steinschliff.pipeline.readme.get_structure_sort_key`.

        Args:
            structure: Структура.

        Returns:
            Ключ сортировки.
        """
        if self.sort_field == "temperature":
            # Сортировка по температуре (сначала самые теплые)
            if structure.temperature and isinstance(structure.temperature, list) and structure.temperature[0]:
                temp_range = structure.temperature[0]
                max_temp = temp_range.get("max")
                if max_temp is not None:
                    try:
                        return -float(max_temp)  # Негативное значение для сортировки по убыванию
                    except (ValueError, TypeError):
                        pass
            # Структуры без температуры отправляем в конец сортировки
            return float("inf")
        # Сортировка по имени или другому полю
        return getattr(structure, self.sort_field, "") or ""

    def _prepare_countries_data(self) -> dict[str, Any]:
        """Подготовить иерархические данные о странах/сервисах для шаблона.

        Returns:
            Словарь формата, ожидаемого шаблонами (`countries`, `ordered_countries`).
        """
        return prepare_countries_data(services=dict(self.services), service_metadata=self.service_metadata)

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
        """Сгенерировать README файлы (ru/en) на основе загруженных данных."""
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
        sort_countries_data_in_place(countries_data=countries_data, sort_field=self.sort_field)

        # Генерируем README для каждого языка
        locales = {
            "en": {"output_file": self.readme_file, "description_field": "description"},
            "ru": {"output_file": self.readme_ru_file, "description_field": "description_ru"},
        }

        for locale, locale_data in locales.items():
            output_file = locale_data["output_file"]
            description_field = locale_data["description_field"]

            # Получаем выходную директорию (для вычисления относительных путей)
            output_dir = Path(output_file).resolve().parent

            # Загружаем переводы для текущей локали
            translations = load_translations(locale)
            # Устанавливаем переводы для Jinja2 через globals, чтобы избежать проблем с типами
            self.jinja_env.add_extension("jinja2.ext.i18n")
            self.jinja_env.globals.update(
                _=translations.gettext, gettext=translations.gettext, ngettext=translations.ngettext
            )

            # Подготавливаем данные для шаблона
            template_data = build_template_data(
                countries_data=countries_data,
                sort_field=self.sort_field,
                output_dir=output_dir,
                language=locale,
                description_field=description_field,
            )

            # Рендерим шаблон
            rendered_content = template.render(**template_data)

            # Записываем результат в файл
            with Path(output_file).open("w", encoding="utf-8") as f:
                f.write(rendered_content)

            # logger.info("README для языка %s успешно сгенерирован в %s", locale.upper(), Path(output_file).resolve())

    def run(self) -> None:
        """Запустить полный цикл генерации README: load → metadata → render."""
        self.load_structures()
        self.load_service_metadata()
        self.generate()
