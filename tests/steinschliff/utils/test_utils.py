import tempfile
from pathlib import Path

import pytest
import yaml

from steinschliff.io.yaml import find_yaml_files, read_service_metadata, read_yaml_file


class TestUtils:
    @pytest.fixture
    def yaml_test_file(self):
        """Создает временный YAML-файл для тестирования."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
            yaml_content = {
                "name": "TestStructure",
                "description": "Test description",
                "snow_type": ["fresh", "old"],
                "snow_temperature": [{"min": -10, "max": 0}],
            }
            yaml.safe_dump(yaml_content, f)
            temp_path = Path(f.name)

        yield str(temp_path)

        # Удаляем файл после теста
        if temp_path.exists():
            temp_path.unlink()

    def test_read_yaml_file(self, yaml_test_file):
        """Тестирует чтение YAML-файла."""
        # Тестируем чтение правильного файла
        data = read_yaml_file(yaml_test_file)
        assert data is not None
        assert data["name"] == "TestStructure"
        assert data["description"] == "Test description"
        assert "fresh" in data["snow_type"]

        # Тестируем чтение несуществующего файла
        data = read_yaml_file("nonexistent_file.yaml")
        assert data is None

        # Тестируем чтение некорректного YAML
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
            f.write("invalid yaml content: [\n")
            invalid_path = Path(f.name)

        try:
            data = read_yaml_file(str(invalid_path))
            assert data is None
        finally:
            if invalid_path.exists():
                invalid_path.unlink()

    def test_find_yaml_files(self):
        """Тестирует поиск YAML-файлов в директории."""
        # Создаем временную директорию со структурой для тестов
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            # Создаем поддиректории
            subdir1 = temp_dir_path / "subdir1"
            subdir2 = temp_dir_path / "subdir2"
            subdir1.mkdir(parents=True)
            subdir2.mkdir(parents=True)

            # Создаем файлы
            yaml_files = [
                temp_dir_path / "file1.yaml",
                subdir1 / "file2.yaml",
                subdir2 / "file3.yaml",
            ]

            non_yaml_file = temp_dir_path / "file.txt"

            # Создаем файлы
            for path in [*yaml_files, non_yaml_file]:
                with Path(path).open("w") as f:
                    f.write("test")

            # Тестируем поиск
            found_files = find_yaml_files(temp_dir)
            assert len(found_files) == len(yaml_files)

            # Проверяем, что все YAML-файлы найдены
            for yaml_file in yaml_files:
                assert any(Path(found_file).samefile(yaml_file) for found_file in found_files)

            # Проверяем, что не-YAML файл не найден
            assert not any(Path(found_file).samefile(non_yaml_file) for found_file in found_files)

    def test_read_service_metadata(self):
        """Тестирует чтение метаданных сервисов."""
        # Создаем временную директорию для теста
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            # Создаем структуру сервисов
            service1_dir = temp_dir_path / "service1"
            service2_dir = temp_dir_path / "service2"
            service1_dir.mkdir(parents=True)
            service2_dir.mkdir(parents=True)

            # Создаем метаданные для первого сервиса
            meta1_path = service1_dir / "_meta.yaml"
            with meta1_path.open("w", encoding="utf-8") as f:
                meta1 = {"name": "Service1", "description": "First service description", "country": "Russia"}
                yaml.safe_dump(meta1, f)

            # Создаем некорректные метаданные для второго сервиса
            meta2_path = service2_dir / "_meta.yaml"
            with meta2_path.open("w", encoding="utf-8") as f:
                f.write("invalid: yaml: [\n")

            # Тестируем чтение метаданных
            services = ["service1", "service2", "service3"]  # service3 не существует
            metadata = read_service_metadata(temp_dir, services)

            # Проверяем результаты
            assert "service1" in metadata
            assert metadata["service1"].name == "Service1"
            assert metadata["service1"].country == "Russia"

            # Сервис с некорректными метаданными теперь тоже присутствует, но с пустыми полями
            assert "service2" in metadata
            assert metadata["service2"].name == "service2"

            # Несуществующий сервис также должен быть пропущен
            assert "service3" not in metadata
