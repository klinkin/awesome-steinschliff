#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import glob
from collections import defaultdict

# Конфигурация
SCHLIFFS_DIR = "schliffs"
README_FILE = "README.md"
README_RU_FILE = "README_ru.md"

def read_yaml_file(file_path):
    """Чтение YAML файла и возврат его содержимого"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Ошибка при чтении {file_path}: {e}")
        return None

def safe_join(items, separator=", "):
    """Безопасное объединение элементов списка в строку"""
    if not items:
        return ""

    # Фильтрация None значений и преобразование всех элементов в строки
    valid_items = [str(item) for item in items if item is not None]
    return separator.join(valid_items)

def generate_readme():
    """Генерация README.md с информацией о структурах"""
    # Словарь для хранения структур по разделам
    sections = defaultdict(list)

    # Поиск всех YAML файлов
    yaml_files = glob.glob(f"{SCHLIFFS_DIR}/**/*.yaml", recursive=True)

    # Обработка каждого файла
    for file_path in yaml_files:
        data = read_yaml_file(file_path)
        if not data:
            continue

        # Определение раздела по директории
        section = os.path.dirname(file_path).replace(f"{SCHLIFFS_DIR}/", "")
        if not section:
            section = "main"

        # Обработка snow_type
        snow_type_value = data.get("snow_type", [])
        if snow_type_value is None:
            snow_type_str = ""
        elif isinstance(snow_type_value, list):
            snow_type_str = safe_join(snow_type_value)
        else:
            snow_type_str = str(snow_type_value)

        # Извлечение необходимой информации
        structure_info = {
            "name": data.get("name", os.path.basename(file_path).replace(".yaml", "")),
            "description": data.get("description", ""),
            "description_ru": data.get("description_ru", ""),
            "snow_type": snow_type_str,
            "house": data.get("house", ""),
            "country": data.get("country", ""),
            "file_path": file_path
        }

        # Добавление информации в соответствующий раздел
        sections[section].append(structure_info)

    # Генерация содержимого README.md
    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write("# Steinschliff Structures\n\n")
        f.write("This repository contains information about various ski grinding structures.\n\n")

        # Оглавление
        f.write("## Table of Contents\n\n")
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            section_anchor = section.lower().replace(" ", "-")
            f.write(f"- [{section_title}](#{section_anchor})\n")
        f.write("\n")

        # Разделы со структурами
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            f.write(f"## {section_title}\n\n")

            # Таблица с структурами
            f.write("| Name | Description | Snow Type | House | Country |\n")
            f.write("|------|------------|-----------|-------|--------|\n")

            # Сортировка структур по имени
            structures = sorted(sections[section], key=lambda x: x["name"])

            for structure in structures:
                description = structure['description'] or ""
                # Экранируем вертикальные черты в описании, чтобы не ломать формат таблицы
                description = description.replace("|", "\\|")
                f.write(f"| {structure['name']} | {description} | {structure['snow_type']} | {structure['house']} | {structure['country']} |\n")

            f.write("\n")

    print(f"README.md generated successfully!")

    # Генерация содержимого README_ru.md
    with open(README_RU_FILE, 'w', encoding='utf-8') as f:
        f.write("# Структуры Steinschliff\n\n")
        f.write("Этот репозиторий содержит информацию о различных структурах для шлифовки лыж.\n\n")

        # Оглавление
        f.write("## Оглавление\n\n")
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            section_anchor = section.lower().replace(" ", "-")
            f.write(f"- [{section_title}](#{section_anchor})\n")
        f.write("\n")

        # Разделы со структурами
        for section in sorted(sections.keys()):
            section_title = section.capitalize()
            f.write(f"## {section_title}\n\n")

            # Таблица с структурами
            f.write("| Название | Описание | Тип снега | Компания | Страна |\n")
            f.write("|----------|----------|-----------|----------|--------|\n")

            # Сортировка структур по имени
            structures = sorted(sections[section], key=lambda x: x["name"])

            for structure in structures:
                description_ru = structure['description_ru'] or ""
                # Экранируем вертикальные черты в описании, чтобы не ломать формат таблицы
                description_ru = description_ru.replace("|", "\\|")
                f.write(f"| {structure['name']} | {description_ru} | {structure['snow_type']} | {structure['house']} | {structure['country']} |\n")

            f.write("\n")

    print(f"README_ru.md generated successfully!")

if __name__ == "__main__":
    generate_readme()