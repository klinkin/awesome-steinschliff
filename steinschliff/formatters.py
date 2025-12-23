"""Функции форматирования для Steinschliff.

Сюда складываем “чистые” функции, которые:
- не читают файлы
- не зависят от Rich/CLI
- преобразуют данные в строки для вывода/шаблонов
"""

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

logger = logging.getLogger("steinschliff.formatters")


def format_list(items: list[str | int | None] | str | None, allow_empty: bool = False) -> str:
    """Отформатировать список значений в строку через запятую.

    Args:
        items: Список элементов, строка или `None`.
        allow_empty: Если `True`, сохраняет пустые строки; иначе пустые строки отбрасываются.

    Returns:
        Строка с элементами, разделёнными запятыми. Для `None`/пустого входа возвращает `""`.
    """
    if not items:
        return ""

    if isinstance(items, list):
        if allow_empty:
            valid_items = [str(item) for item in items if item is not None]
        else:
            valid_items = [str(item) for item in items if item is not None and str(item).strip() != ""]
        return ", ".join(valid_items)

    return str(items)


# Для обратной совместимости определяем функции через универсальную
def format_snow_types(items: list[str | int | None] | str | None) -> str:
    """Отформатировать список типов снега, разрешая пустые строки.

    Args:
        items: Типы снега.

    Returns:
        Отформатированная строка (значения через запятую).
    """
    return format_list(items, allow_empty=True)


# Алиас для format_list
format_list_for_display = format_list

# Алиас для format_list
format_features = format_list


def url_encode_path(path_value: str | Path) -> str:
    """Закодировать путь для использования в Markdown-ссылках.

    Эквивалент `urllib.parse.quote`, но со сохранением разделителей директорий (`/`).

    Args:
        path_value: Путь (строка или `Path`).

    Returns:
        URL-кодированная строка пути.
    """
    # Преобразуем в строку и кодируем, сохраняя слэши
    return quote(str(path_value), safe="/")


def format_similars_with_links(
    similars: list[str | int | None] | str | None,
    generator,
    output_dir: str,
) -> str:
    """Отформатировать “похожие структуры” со ссылками на их YAML-файлы.

    Args:
        similars: Список имён похожих структур, строка или `None`.
        generator: Объект с методом `get_path_by_name(name: str) -> str | None`.
        output_dir: Директория, относительно которой строятся ссылки (директория README).

    Returns:
        Строка вида `"[S1](path/to/S1.yaml), S2"` или `""`, если вход пуст.
        Если `similars` не список — возвращает `str(similars)`.
    """
    if not similars:
        return ""

    # Если это не список, просто возвращаем строковое представление
    if not isinstance(similars, list):
        return str(similars)

    result = []
    output_path = Path(output_dir)

    for item in similars:
        if item is None or str(item).strip() == "":
            continue

        # Конвертируем элемент в строку для поиска
        str_item = str(item)
        path = generator.get_path_by_name(str_item)

        if path:
            # Конвертируем в относительный путь от файла README
            path_obj = Path(path)
            try:
                # Создаем относительный путь если возможно
                if path_obj.is_relative_to(output_path):
                    rel_path = path_obj.relative_to(output_path)
                else:
                    rel_path = path_obj.relative_to(Path.cwd())
            except ValueError:
                # Если не удалось создать относительный путь, используем os.path.relpath
                rel_path = Path(os.path.relpath(path, output_dir))
            # Кодируем путь для корректной работы Markdown при пробелах
            encoded_path = url_encode_path(rel_path)
            result.append(f"[{str_item}]({encoded_path})")
        else:
            result.append(str_item)

    return ", ".join(result)


def format_temperature_range(
    temperature: list[dict[str, Any]] | None,
) -> str:
    """Отформатировать диапазон температуры для отображения в таблице.

    Формат: `"max °C … min °C"`. В предметной области сначала указывается более тёплая
    температура, затем более холодная.

    Args:
        temperature: Список диапазонов температуры (используется только первый элемент).

    Returns:
        Отформатированная строка или `""` для пустого/некорректного входа.
    """
    if not temperature or not isinstance(temperature, list) or not temperature[0]:
        return ""

    try:
        # Берем только первый диапазон (если их несколько)
        temp_range = temperature[0]
        min_temp = temp_range.get("min")
        max_temp = temp_range.get("max")

        # Если min или max отсутствуют, возвращаем пустую строку
        if min_temp is None or max_temp is None:
            return ""

        # Убираем .0 в конце для целых чисел
        if isinstance(min_temp, int | float):
            min_temp_str = str(int(min_temp)) if min_temp == int(min_temp) else str(min_temp)
        else:
            min_temp_str = str(min_temp)

        if isinstance(max_temp, int | float):
            max_temp_str = str(int(max_temp)) if max_temp == int(max_temp) else str(max_temp)
        else:
            max_temp_str = str(max_temp)

        # Заменяем минус на типографский
        if min_temp_str.startswith("-"):
            min_temp_str = "–" + min_temp_str[1:]
        elif float(min_temp) > 0:
            min_temp_str = "+" + min_temp_str

        if max_temp_str.startswith("-"):
            max_temp_str = "–" + max_temp_str[1:]
        elif float(max_temp) > 0:
            max_temp_str = "+" + max_temp_str

        # Форматируем в виде диапазона с градусами и многоточием
        # В соответствии с предметной областью: сначала более теплая температура, затем более холодная
        return f"{max_temp_str} °C … {min_temp_str} °C"
    except (ValueError, TypeError) as e:
        logger.warning("Ошибка при форматировании температурного диапазона: %s", e)
        return ""


def format_image_link(image_value: str | list[str], structure_name: str, output_dir: str) -> str:
    """Сформировать Markdown-ссылку на изображение структуры.

    Args:
        image_value: Путь к изображению или список путей (берётся первый элемент).
        structure_name: Имя структуры (используется как alt-текст).
        output_dir: Директория вывода (для построения относительных путей).

    Returns:
        Markdown-строка вида `![Name](path/to/img.jpg)` или `""` для некорректного входа.
    """
    try:
        # Проверка на пустое значение
        if not image_value:
            return ""

        # Если image_value это список, берём первый элемент, если список не пустой
        if isinstance(image_value, list):
            if not image_value:  # Проверка на пустой список
                return ""
            path = image_value[0]
        else:
            path = image_value

        # Проверяем, что путь не пустой и является строкой
        if not path or not isinstance(path, str):
            return ""

        # Создаём объекты Path
        path_obj = Path(path)
        output_path = Path(output_dir)

        # Создаём относительный путь (безопасно, с обработкой ошибок)
        try:
            # Пробуем создать относительный путь напрямую
            if path_obj.is_absolute() and output_path.is_absolute():
                # Для абсолютных путей пробуем создать относительный путь
                relative_path = path_obj.relative_to(output_path) if path_obj.is_relative_to(output_path) else path_obj
            else:
                # Для относительных путей
                relative_path = path_obj.relative_to(output_path) if path_obj.is_relative_to(output_path) else path_obj
        except ValueError:
            # Если не удалось создать относительный путь, возвращаемся к os.path.relpath
            relative_path = Path(os.path.relpath(path, output_dir))

        # Возвращаем форматированную ссылку в синтаксисе Markdown
        # Кодируем путь для корректной работы Markdown при пробелах в сегментах
        encoded_path = url_encode_path(relative_path)
        return f"![{structure_name}]({encoded_path})"
    except (ValueError, OSError, TypeError) as e:
        logger.error("Ошибка при форматировании изображения %s: %s", image_value, e)
        return ""
