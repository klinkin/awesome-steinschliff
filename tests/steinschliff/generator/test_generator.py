import os
import tempfile
from collections import defaultdict
from pathlib import Path

import pytest
import yaml

from steinschliff.config import GeneratorConfig
from steinschliff.generator import ReadmeGenerator
from steinschliff.pipeline.readme import load_structures_from_yaml_files


class TestProcessYamlFiles:
    @pytest.fixture
    def setup_test_files(self):
        """Создает временную директорию с тестовыми YAML-файлами."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем тестовую структуру директорий
            service1_dir = os.path.join(temp_dir, "service1")
            service2_dir = os.path.join(temp_dir, "service2")
            os.makedirs(service1_dir)
            os.makedirs(service2_dir)

            # Создаем тестовые файлы
            test_files = {
                os.path.join(service1_dir, "struct1.yaml"): {
                    "name": "Structure1",
                    "description": "Test description",
                    "description_ru": "Тестовое описание",
                    "snow_type": ["fresh", "transformed"],
                    "snow_temperature": [{"min": -15, "max": -5}],
                    "country": "Россия",
                    "tags": ["tag1", "tag2"],
                },
                os.path.join(service1_dir, "struct2.yaml"): {
                    "name": "Structure2",
                    "description": "Another description",
                    "snow_type": ["old"],
                    "service": {"name": "TestService"},
                },
                os.path.join(service2_dir, "struct3.yaml"): {
                    "name": "Structure3",
                    "description": "Third description",
                    "similars": ["Structure1", "Structure2"],
                },
                # Файл с ошибкой
                os.path.join(service2_dir, "invalid.yaml"): "invalid: yaml: content",
                # Мета-файл, который должен быть пропущен
                os.path.join(service1_dir, "_meta.yaml"): {"name": "Service1", "description": "Test service"},
            }

            # Записываем содержимое в файлы
            for file_path, content in test_files.items():
                with open(file_path, "w", encoding="utf-8") as f:
                    if isinstance(content, dict):
                        yaml.safe_dump(content, f, allow_unicode=True)
                    else:
                        f.write(content)

            yield temp_dir

    def test_process_yaml_files(self, setup_test_files, caplog):
        """
        Тестирует метод _process_yaml_files ReadmeGenerator.

        Проверяет:
        1. Корректное создание name_to_path
        2. Корректную обработку структур сервисов
        3. Правильную обработку ошибок
        4. Пропуск _meta.yaml файлов
        """
        # Подготовка генератора с минимальной конфигурацией
        config = GeneratorConfig(
            schliffs_dir=setup_test_files,
            readme_file=os.path.join(setup_test_files, "README.md"),
            readme_ru_file=os.path.join(setup_test_files, "README_ru.md"),
        )
        generator = ReadmeGenerator(config)

        # Находим все YAML-файлы
        yaml_files = [
            os.path.join(dirpath, f)
            for dirpath, _, files in os.walk(setup_test_files)
            for f in files
            if f.endswith(".yaml")
        ]

        # Шаг LOAD+VALIDATE вынесен в pipeline (и тестируется отдельно)
        loaded = load_structures_from_yaml_files(
            yaml_files=[Path(p) for p in yaml_files],
            schliffs_dir=Path(setup_test_files),
        )
        generator.services = defaultdict(list, loaded.services)
        generator.name_to_path = loaded.name_to_path

        # Проверяем результаты

        # 1. Проверяем name_to_path
        assert len(generator.name_to_path) == 3
        assert "Structure1" in generator.name_to_path
        assert "Structure2" in generator.name_to_path
        assert "Structure3" in generator.name_to_path

        # 2. Проверяем services
        assert len(generator.services) == 2
        assert "service1" in generator.services
        assert "service2" in generator.services

        # Проверяем структуры в первом сервисе
        assert len(generator.services["service1"]) == 2
        structure1 = next(s for s in generator.services["service1"] if s.name == "Structure1")
        assert structure1.description == "Test description"
        assert structure1.country == "Россия"
        assert len(structure1.tags) == 2

        # Проверяем структуры во втором сервисе
        assert len(generator.services["service2"]) == 1
        structure3 = generator.services["service2"][0]
        assert structure3.name == "Structure3"
        assert len(structure3.similars) == 2

        # 3. Проверяем обработку ошибок через caplog
        assert any(
            "Ошибка разбора YAML" in record.message and "invalid.yaml" in record.message for record in caplog.records
        )

        # 4. Проверяем, что в результатах нет _meta.yaml
        all_structures = [s.name for service in generator.services.values() for s in service]
        assert "Service1" not in all_structures

    def test_name_to_path_propagation(self, setup_test_files):
        """
        Проверяет, что словарь name_to_path в ReadmeGenerator корректен.
        """
        # Подготовка генератора
        config = GeneratorConfig(
            schliffs_dir=setup_test_files,
            readme_file=os.path.join(setup_test_files, "README.md"),
            readme_ru_file=os.path.join(setup_test_files, "README_ru.md"),
        )
        generator = ReadmeGenerator(config)

        # Находим все YAML-файлы
        yaml_files = [
            os.path.join(dirpath, f)
            for dirpath, _, files in os.walk(setup_test_files)
            for f in files
            if f.endswith(".yaml")
        ]

        loaded = load_structures_from_yaml_files(
            yaml_files=[Path(p) for p in yaml_files],
            schliffs_dir=Path(setup_test_files),
        )
        generator.services = defaultdict(list, loaded.services)
        generator.name_to_path = loaded.name_to_path

        # Проверяем, что name_to_path содержит все структуры
        assert len(generator.name_to_path) == 3

        # Проверяем, что метод get_path_by_name корректно работает
        for name, path in generator.name_to_path.items():
            assert generator.get_path_by_name(name) == path
            assert os.path.exists(path)


class TestGenerate:
    @pytest.fixture
    def setup_generate_files(self):
        """Создает временную директорию с сервисом и метаданными для теста generate."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service_dir = os.path.join(temp_dir, "service1")
            os.makedirs(service_dir)

            structures = {
                os.path.join(service_dir, "z.yaml"): {"name": "Zeta", "description": "Z"},
                os.path.join(service_dir, "a.yaml"): {"name": "Alpha", "description": "A"},
            }

            for path, content in structures.items():
                with open(path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(content, f, allow_unicode=True)

            meta = {
                "name": "Service 1",
                "description": "Some description",
                "country": "Россия",
                "contact": {"email": "info@example.com"},
            }
            with open(os.path.join(service_dir, "_meta.yaml"), "w", encoding="utf-8") as f:
                yaml.safe_dump(meta, f, allow_unicode=True)

            yield temp_dir

    def test_generate_creates_readme_and_uses_metadata(self, setup_generate_files):
        config = GeneratorConfig(
            schliffs_dir=setup_generate_files,
            readme_file=os.path.join(setup_generate_files, "README.md"),
            readme_ru_file=os.path.join(setup_generate_files, "README_ru.md"),
        )
        generator = ReadmeGenerator(config)
        generator.load_structures()
        generator.load_service_metadata()
        generator.generate()

        readme_path = os.path.join(setup_generate_files, "README.md")
        assert os.path.exists(readme_path)
        with open(readme_path, encoding="utf-8") as f:
            content = f.read()

        assert "Some description" in content
        assert "info@example.com" in content
        assert content.index("Alpha") < content.index("Zeta")
