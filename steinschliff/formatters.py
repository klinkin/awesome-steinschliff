"""
Функции форматирования для Steinschliff.
"""

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

logger = logging.getLogger("steinschliff.formatters")


def format_list(items: list[str | int | None] | str | None, allow_empty: bool = False) -> str:
    """
    Универсальная функция для форматирования списков элементов в строку.

    Args:
        items: Список элементов, строка или None.
        allow_empty: Разрешать ли пустые строки в списке.

    Returns:
        Отформатированная строка с элементами, разделенными запятыми.
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
    """Форматирует список типов снега, разрешая пустые строки."""
    return format_list(items, allow_empty=True)


# Алиас для format_list
format_list_for_display = format_list

# Алиас для format_list
format_features = format_list


def url_encode_path(path_value: str | Path) -> str:
    """
    Возвращает URL-кодированное представление пути для использования в Markdown-ссылках.

    Эквивалент urllib.parse.quote с сохранением разделителей директорий.
    """
    # Преобразуем в строку и кодируем, сохраняя слэши
    return quote(str(path_value), safe="/")


def format_similars_with_links(
    similars: list[str | int | None] | str | None,
    generator,
    output_dir: str,
) -> str:
    """
    Форматирует список похожих структур со ссылками на их файлы.

    Args:
        similars: Список названий похожих структур, строка или None.
        generator: Экземпляр ReadmeGenerator для получения путей по именам.
        output_dir: Директория, в которой будет сохранен файл README.

    Returns:
        Отформатированная строка со ссылками на похожие структуры, разделенные запятыми.
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
    snow_temperature: list[dict[str, Any]] | None,
) -> str:
    """
    Форматирует диапазон температуры снега для отображения в таблице в формате "max °C … min °C".
    В соответствии с предметной областью, сначала указывается более теплая температура, затем более холодная.
    Пример: "+1 °C … –8 °C" или "–3 °C … –5 °C"

    Args:
        snow_temperature: Список диапазонов температуры снега.

    Returns:
        Отформатированная строка с диапазоном температуры в формате "max °C … min °C".
    """
    if not snow_temperature or not isinstance(snow_temperature, list) or not snow_temperature[0]:
        return ""

    try:
        # Берем только первый диапазон (если их несколько)
        temp_range = snow_temperature[0]
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
    """
    Форматирует изображение для отображения в Markdown.

    Args:
        image_value: Путь к изображению или список путей к изображениям
        structure_name: Имя структуры (используется как alt-текст для изображения)
        output_dir: Директория для вывода (используется для создания относительных путей)

    Returns:
        Форматированная строка Markdown для изображения
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
