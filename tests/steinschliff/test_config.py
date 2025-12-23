from pathlib import Path

import pytest
from pydantic import ValidationError

from steinschliff.config import GeneratorConfig


def test_generator_config_defaults_and_paths(tmp_path: Path):
    cfg = GeneratorConfig(
        schliffs_dir=tmp_path / "schliffs",
        readme_file=tmp_path / "README_en.md",
        readme_ru_file=tmp_path / "README.md",
    )
    assert cfg.sort_field == "name"
    assert isinstance(cfg.schliffs_dir, Path)


def test_generator_config_as_dict_is_compatible(tmp_path: Path):
    cfg = GeneratorConfig(
        schliffs_dir=tmp_path / "schliffs",
        readme_file=tmp_path / "README_en.md",
        readme_ru_file=tmp_path / "README.md",
        sort_field="temperature",
        translations_dir=tmp_path / "translations",
    )
    d = cfg.as_dict()
    assert d["sort_field"] == "temperature"
    assert d["schliffs_dir"].endswith("schliffs")


def test_generator_config_requires_fields():
    with pytest.raises(ValidationError):
        GeneratorConfig()  # type: ignore[call-arg]
