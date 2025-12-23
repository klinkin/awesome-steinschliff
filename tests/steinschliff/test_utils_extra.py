from unittest.mock import patch

from steinschliff.io.yaml import read_service_metadata, read_yaml_file
from steinschliff.ui.rich import print_validation_summary


def test_print_validation_summary_info(caplog):
    # Лишь проверяем, что не падает и что логируется INFO-сообщение
    caplog.set_level("INFO")
    print_validation_summary(3, 1, 2)
    assert any("РЕЗУЛЬТАТЫ ВАЛИДАЦИИ YAML-ФАЙЛОВ" in r.message for r in caplog.records)


def test_read_yaml_file_invalid_yaml(tmp_path):
    # Некорректный YAML -> None
    p = tmp_path / "bad.yaml"
    p.write_text("invalid: [\n", encoding="utf-8")
    assert read_yaml_file(str(p)) is None


def test_read_yaml_file_non_mapping_yaml(tmp_path):
    # YAML-список вместо объекта -> None
    p = tmp_path / "list.yaml"
    p.write_text("- 1\n- 2\n", encoding="utf-8")
    assert read_yaml_file(str(p)) is None


def test_read_yaml_file_not_found():
    assert read_yaml_file("/path/does/not/exist.yaml") is None


def test_read_service_metadata_warnings_and_errors(tmp_path, caplog):
    caplog.set_level("INFO")

    root = tmp_path
    s1 = root / "svc1"
    s2 = root / "svc2"
    s3 = root / "svc3"
    for d in (s1, s2, s3):
        d.mkdir()

    # svc1: пустой или невалидный -> предупреждение
    (s1 / "_meta.yaml").write_text("invalid: [\n", encoding="utf-8")

    # svc2: нормальный файл (но минимальный)
    (s2 / "_meta.yaml").write_text("name: S2\n", encoding="utf-8")

    # svc3: смоделируем ошибку чтения через мок
    (s3 / "_meta.yaml").write_text("name: S3\n", encoding="utf-8")

    services = ["svc1", "svc2", "svc3"]

    with patch("steinschliff.io.yaml.read_yaml_file") as mocked:

        def side_effect(path):
            if str(path).endswith("svc1/_meta.yaml"):
                return None  # предупреждение
            if str(path).endswith("svc3/_meta.yaml"):
                raise OSError("boom")  # попадет в metadata_errors (обрабатывается)
            return {"name": "S2"}

        mocked.side_effect = side_effect
        meta = read_service_metadata(str(root), services)

    # svc2 инициализировался с валидными данными
    assert "svc2" in meta
    # svc1 и svc3 должны логироваться как проблемные
    assert any("Пустые файлы метаданных" in r.message for r in caplog.records) or any(
        "Пустые файлы" in r.message for r in caplog.records
    )
    assert any("Ошибка чтения метаданных" in r.message for r in caplog.records)
