from pathlib import Path

import yaml

from steinschliff.io.yaml import read_yaml_file


def _write_yaml(path, data) -> None:
    with Path(path).open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True)


def test_read_yaml_file_marks_partial_validation_when_required_fields_present(tmp_path):
    # Файл намеренно "почти валидный": есть name/description, но есть и сломанный тип поля.
    # Ожидаем: read_yaml_file вернёт dict и пометит _partial_validation=True (вместо None).
    p = tmp_path / "partial.yaml"
    _write_yaml(
        p,
        {
            "name": "S1",
            "description": "desc",
            "temperature": "not-a-list",  # провоцируем ValidationError в SchliffStructure
        },
    )

    data = read_yaml_file(str(p))
    assert isinstance(data, dict)
    assert data.get("_partial_validation") is True
    assert data.get("name") == "S1"


def test_read_yaml_file_returns_none_when_required_fields_missing(tmp_path):
    # Нет name/description => после ValidationError файл считается непригодным и возвращается None.
    p = tmp_path / "invalid.yaml"
    _write_yaml(p, {"temperature": "not-a-list"})
    assert read_yaml_file(str(p)) is None
