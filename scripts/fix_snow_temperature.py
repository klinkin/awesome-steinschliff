#!/usr/bin/env python3
"""
Скрипт для исправления формата поля snow_temperature в YAML-файлах.

Исправляет формат с:
snow_temperature:
  - min: -10
  - max: 0

На правильный:
snow_temperature:
  - min: -10
    max: 0
"""

import os
import re
import glob
import yaml
import argparse

def fix_snow_temperature_format(yaml_file, dry_run=False):
    """
    Исправляет формат поля snow_temperature в указанном YAML-файле.

    Args:
        yaml_file: Путь к YAML-файлу
        dry_run: Если True, только показывает изменения, но не применяет их

    Returns:
        True если файл был изменен, False в противном случае
    """
    # Если это мета-файл, пропускаем
    if os.path.basename(yaml_file) == "_meta.yaml":
        return False

    # Читаем содержимое файла
    with open(yaml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем наличие поля snow_temperature
    if 'snow_temperature:' not in content:
        return False

    # Проверяем текущий формат и исправляем его, если нужно
    pattern = r'snow_temperature:\s*\n\s*- min: ([^\n]*)\s*\n\s*- max: ([^\n]*)'
    match = re.search(pattern, content)

    if match:
        min_value = match.group(1)
        max_value = match.group(2)

        # Формируем новое содержимое
        new_pattern = f'snow_temperature:\n  - min: {min_value}\n    max: {max_value}'
        new_content = re.sub(pattern, new_pattern, content)

        if new_content != content:
            print(f"Исправляем {yaml_file}:")
            print(f"  БЫЛО: min: {min_value}, max: {max_value} (отдельные элементы)")
            print(f"  СТАЛО: min: {min_value}, max: {max_value} (в одном элементе)")

            if not dry_run:
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            return True

    return False

def find_all_yaml_files(directory):
    """Находит все YAML-файлы в указанной директории и поддиректориях."""
    return glob.glob(os.path.join(directory, '**', '*.yaml'), recursive=True)

def main():
    parser = argparse.ArgumentParser(description='Исправляет формат поля snow_temperature в YAML-файлах')
    parser.add_argument('--dir', default='schliffs', help='Директория с YAML-файлами')
    parser.add_argument('--dry-run', action='store_true', help='Не изменять файлы, только показать изменения')
    args = parser.parse_args()

    yaml_files = find_all_yaml_files(args.dir)
    print(f"Найдено {len(yaml_files)} YAML-файлов")

    fixed_count = 0
    for yaml_file in yaml_files:
        if fix_snow_temperature_format(yaml_file, args.dry_run):
            fixed_count += 1

    print(f"\nВсего исправлено файлов: {fixed_count}")
    if args.dry_run:
        print("(Был режим симуляции, изменения не были сохранены)")

if __name__ == "__main__":
    main()