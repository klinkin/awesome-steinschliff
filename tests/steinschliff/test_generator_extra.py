import yaml

from steinschliff.export.json import export_structures_json
from steinschliff.generator import ReadmeGenerator


def _write_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True)


def test_sort_by_temperature_and_export_json(tmp_path):
    # Структура директорий и файлов
    root = tmp_path
    svc = root / "svc"
    svc.mkdir()

    warm = svc / "warm.yaml"
    cold = svc / "cold.yaml"
    none_temp = svc / "none.yaml"

    _write_yaml(
        warm,
        {
            "name": "Warm",
            "description": "",
            "temperature": [{"min": -5, "max": 5}],
        },
    )
    _write_yaml(
        cold,
        {
            "name": "Cold",
            "description": "",
            "temperature": [{"min": -20, "max": -5}],
        },
    )
    _write_yaml(
        none_temp,
        {
            "name": "NoTemp",
            "description": "",
        },
    )

    # Мета-файл, чтобы не влиять на сортировку
    _write_yaml(svc / "_meta.yaml", {"name": "Service", "country": "Россия"})

    config = {
        "schliffs_dir": str(root),
        "readme_file": str(root / "README.md"),
        "readme_ru_file": str(root / "README_ru.md"),
        "sort_field": "temperature",
    }

    gen = ReadmeGenerator(config)
    gen.load_structures()
    gen.load_service_metadata()

    # Проверяем сортировку: теплые должны идти раньше холодных, а без температуры — в конце
    countries_data = gen._prepare_countries_data()
    svc_structs = countries_data["countries"]["Россия"]["services"]["svc"]["structures"]

    # До генерации сортировка не применена; применится в generate. Применим вручную ключ
    ordered = sorted(svc_structs, key=gen._get_structure_sort_key)
    assert [s.name for s in ordered] == ["Warm", "Cold", "NoTemp"]

    # Проверим экспорт JSON
    out_json = root / "out" / "data.json"
    export_structures_json(services={"svc": ordered}, out_path=str(out_json))
    assert out_json.exists()
