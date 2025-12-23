"""
I/O слой проекта: чтение файлов, парсинг и базовая валидация входных данных.

Здесь живут функции, которые работают с файловой системой и внешними форматами (YAML).
"""

from .yaml import find_yaml_files, read_service_metadata, read_yaml_file

__all__ = ["find_yaml_files", "read_service_metadata", "read_yaml_file"]
