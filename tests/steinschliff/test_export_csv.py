from steinschliff.export.csv import export_structures_csv_string
from steinschliff.models import Service, StructureInfo


def test_export_structures_csv_string_contains_header_and_row():
    s1 = StructureInfo(
        name="S1",
        snow_type="fresh",
        temperature=[{"min": -5, "max": 0}],
        condition="blue",
        service=Service(name="svc"),
        country="Россия",
        tags=["t1"],
        similars=["x"],
        features=[],
        images=[],
        file_path="schliffs/svc/S1.yaml",
    )

    content = export_structures_csv_string(services={"svc": [s1]})
    assert "Сервис,Имя,Тип снега,Условия,Температура,Похожие" in content
    assert "svc" in content
    assert "S1" in content
