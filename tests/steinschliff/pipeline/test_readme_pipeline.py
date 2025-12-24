from pathlib import Path

import yaml

from steinschliff.models import ServiceMetadata, StructureInfo
from steinschliff.pipeline.readme import (
    get_structure_sort_key,
    load_structures_from_yaml_files,
    prepare_countries_data,
    sort_countries_data_in_place,
)


def _write_yaml(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True)


def test_load_structures_from_yaml_files_collects_services_and_stats(tmp_path: Path):
    root = tmp_path
    svc = root / "svc"
    svc.mkdir()

    _write_yaml(svc / "ok.yaml", {"name": "S1", "description": "d", "temperature": [{"min": -5, "max": 0}]})
    # Плохой YAML
    (svc / "bad.yaml").write_text("invalid: [\n", encoding="utf-8")
    # meta должен игнорироваться
    _write_yaml(svc / "_meta.yaml", {"name": "Service"})

    loaded = load_structures_from_yaml_files(
        yaml_files=[svc / "ok.yaml", svc / "bad.yaml", svc / "_meta.yaml"],
        schliffs_dir=root,
    )

    assert "svc" in loaded.services
    assert loaded.stats.processed_structures == 1
    assert loaded.stats.error_files == 1
    assert loaded.stats.valid_files + loaded.stats.warning_files == 1
    assert "S1" in loaded.name_to_path


def test_prepare_countries_data_orders_russia_first():
    services = {
        "svc1": [StructureInfo(name="A", file_path="a")],
        "svc2": [StructureInfo(name="B", file_path="b")],
    }
    meta = {
        "svc1": ServiceMetadata(name="Svc1", country="Россия"),
        "svc2": ServiceMetadata(name="Svc2", country="Австрия"),
    }

    countries_data = prepare_countries_data(services=services, service_metadata=meta)
    assert countries_data["ordered_countries"][0] == "Россия"


def test_sort_key_and_sort_countries_data_by_temperature():
    warm = StructureInfo(name="Warm", temperature=[{"min": -5, "max": 5}], file_path="w")
    cold = StructureInfo(name="Cold", temperature=[{"min": -20, "max": -5}], file_path="c")
    none = StructureInfo(name="None", file_path="n")

    assert get_structure_sort_key(sort_field="temperature", structure=warm) < get_structure_sort_key(
        sort_field="temperature", structure=cold
    )
    assert get_structure_sort_key(sort_field="temperature", structure=none) == float("inf")

    countries_data = {
        "countries": {"Россия": {"services": {"svc": {"structures": [cold, none, warm]}}}},
        "ordered_countries": ["Россия"],
    }
    sort_countries_data_in_place(countries_data=countries_data, sort_field="temperature")
    ordered = countries_data["countries"]["Россия"]["services"]["svc"]["structures"]
    assert [s.name for s in ordered] == ["Warm", "Cold", "None"]
