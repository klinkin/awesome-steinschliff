"""
Функции форматирования для Steinschliff.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("steinschliff.formatters")


def format_snow_types(snow_types: Union[List[str], str, None]) -> str:
    """
    Форматирует список типов снега для отображения в таблицах README.

    Args:
        snow_types: Список типов снега или строка.

    Returns:
        Отформатированная строка с типами снега, разделенными запятыми.
    """
    if not snow_types:
        return ""

    if isinstance(snow_types, list):
        # Фильтруем значения None и конвертируем в строки
        valid_types = [str(item) for item in snow_types if item is not None]
        return ", ".join(valid_types)

    return str(snow_types)


def format_list_for_display(
    items: Union[List[Union[str, int, None]], str, None],
) -> str:
    """
    Форматирует список элементов для отображения в таблицах README.

    Args:
        items: Список элементов, строка или None.

    Returns:
        Отформатированная строка с элементами, разделенными запятыми.
    """
    if not items:
        return ""

    if isinstance(items, list):
        # Фильтруем значения None и пустые строки, затем конвертируем в строки
        valid_items = [str(item) for item in items if item is not None and str(item).strip() != ""]
        return ", ".join(valid_items)

    return str(items)


def format_similars_with_links(
    similars: Union[List[Union[str, int, None]], str, None],
    name_to_path: Dict[str, str],
    output_dir: str,
) -> str:
    """
    Форматирует список похожих структур со ссылками на их файлы.

    Args:
        similars: Список названий похожих структур, строка или None.
        name_to_path: Словарь, сопоставляющий названия структур с путями к файлам.
        output_dir: Директория, в которой будет сохранен файл README.

    Returns:
        Отформатированная строка со ссылками на похожие структуры, разделенные запятыми.
    """
    if not similars:
        return ""

    # Конвертируем все ключи в словаре name_to_path в строки для безопасного поиска
    str_name_to_path = {str(k): v for k, v in name_to_path.items()}

    result = []
    if isinstance(similars, list):
        for item in similars:
            if item is None or str(item).strip() == "":
                continue

            # Конвертируем элемент в строку для поиска
            str_item = str(item)
            if str_item in str_name_to_path:
                # Конвертируем в относительный путь от файла README
                rel_path = os.path.relpath(str_name_to_path[str_item], start=output_dir)
                result.append(f"[{str_item}]({rel_path})")
            else:
                result.append(str_item)
    else:
        # Если это одиночная строка, просто возвращаем ее
        return str(similars)

    return ", ".join(result)


def format_temperature_range(
    snow_temperature: Union[List[Dict[str, Any]], None],
) -> str:
    """
    Форматирует диапазон температуры снега для отображения в таблице в формате "max min".
    Пример: "+3 -3" или "-1 -6"

    Args:
        snow_temperature: Список диапазонов температуры снега.

    Returns:
        Отформатированная строка с диапазоном температуры в формате "max min".
    """
    if not snow_temperature:
        return ""

    try:
        # Берем только первый диапазон (если их несколько)
        temp_range = snow_temperature[0]
        min_temp = temp_range.get("min")
        max_temp = temp_range.get("max")

        # Если min или max отсутствуют, возвращаем пустую строку
        if min_temp is None or max_temp is None:
            return ""

        # Форматируем числа, добавляя + к положительным
        min_temp_str = f"+{min_temp}" if float(min_temp) > 0 else str(min_temp)
        max_temp_str = f"+{max_temp}" if float(max_temp) > 0 else str(max_temp)

        # Убираем .0 в конце для целых чисел
        min_temp_str = min_temp_str.replace(".0", "")
        max_temp_str = max_temp_str.replace(".0", "")

        # Форматируем как "max min"
        result = f"{max_temp_str} {min_temp_str}"
        logger.debug(f"Отформатированный диапазон температуры: {result}")
        return result
    except Exception as e:
        logger.warning(f"Ошибка при форматировании температурного диапазона: {e}")
        return ""


def format_image_link(image_value, structure_name: str, output_dir: str) -> str:
    """
    Форматирует ссылку на изображение для отображения в таблице.

    Args:
        image_value: Значение поля image (может быть строкой или списком строк)
        structure_name: Название структуры
        output_dir: Директория, относительно которой вычисляются относительные пути

    Returns:
        Отформатированная ссылка на изображение
    """
    if not image_value:
        return ""

    # Если передан список изображений, обрабатываем его
    if isinstance(image_value, list):
        # Возвращаем список в формате строки, как в оригинальном скрипте
        return str(image_value)

    # Если передана одна строка, обрабатываем ее
    try:
        # Вычисляем относительный путь
        if output_dir:
            relative_path = os.path.relpath(image_value, output_dir)
        else:
            relative_path = image_value

        # Форматируем HTML с изображением
        return f'<img src="{relative_path}" alt="{structure_name}" width="100">'
    except Exception as e:
        logger.error(f"Ошибка форматирования ссылки на изображение: {e}")
        return image_value


def format_features(features: Union[List[str], None]) -> str:
    """
    Форматирует список особенностей структуры для отображения в таблицах README.

    Args:
        features: Список особенностей.

    Returns:
        Отформатированная строка с особенностями, разделенными запятыми.
    """
    if not features:
        return ""

    if isinstance(features, list):
        # Фильтруем значения None и пустые строки, затем конвертируем в строки
        valid_features = [str(item) for item in features if item is not None and str(item).strip() != ""]
        return ", ".join(valid_features)

    # Если это строка, просто возвращаем ее
    return str(features)
