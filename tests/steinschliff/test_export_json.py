import json

from steinschliff.export.json import export_structures_json
from steinschliff.models import Service, StructureInfo


def test_export_structures_json_writes_file(tmp_path):
    out = tmp_path / "out" / "structures.json"

    s1 = StructureInfo(
        name="S1",
        snow_type="fresh",
        temperature=[{"min": -5, "max": 0}],
        condition="blue",
        service=Service(name="svc"),
        country="Россия",
        tags=["t1", None, ""],
        similars=["x", ""],
        features=["f1"],
        images=[],
        file_path="schliffs/svc/S1.yaml",
    )

    export_structures_json(services={"svc": [s1]}, out_path=str(out))
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["name"] == "S1"
    assert data[0]["service"] == "svc"
    assert data[0]["temp_min"] == -5
    assert data[0]["temp_max"] == 0
    assert data[0]["tags"] == ["t1"]
