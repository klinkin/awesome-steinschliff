from types import SimpleNamespace

import pytest

from steinschliff.formatters import (
    format_features,
    format_image_link,
    format_list,
    format_list_for_display,
    format_similars_with_links,
    format_snow_types,
    format_temperature_range,
)


def test_format_list_basic_cases():
    assert format_list(None) == ""
    assert format_list([]) == ""
    assert format_list(["a", "b"]) == "a, b"
    assert format_list(["a", None, "", "b"]) == "a, b"
    assert format_list(["a", None, "", "b"], allow_empty=True) == "a, , b"
    assert format_list(123) == "123"


def test_aliases_behave_like_format_list():
    assert format_list_for_display(["x", None, "y"]) == "x, y"
    assert format_features(["x", "", None, "y"]) == "x, y"
    assert format_snow_types(["fresh", "", None, "old"]) == "fresh, , old"


@pytest.mark.parametrize(
    ("temp", "expected"),
    [
        ([{"min": -8, "max": 1}], "+1 °C … –8 °C"),
        ([{"min": -10.0, "max": 0.0}], "0 °C … –10 °C"),
        ([{"min": 2, "max": 5}], "+5 °C … +2 °C"),
    ],
)
def test_format_temperature_range_ok(temp, expected):
    assert format_temperature_range(temp) == expected


@pytest.mark.parametrize(
    "payload",
    [None, [], [{}], [{"min": None, "max": 1}], [{"min": 1, "max": None}], [{"min": "x", "max": 1}]],
)
def test_format_temperature_range_edge_cases(payload):
    assert format_temperature_range(payload) == ""


def test_format_temperature_range_string_numbers_are_supported():
    # Ветка: min/max приходят как строки -> должны обработаться через float(...) и префиксы +/-.
    assert format_temperature_range([{"min": "0", "max": "1"}]) == "+1 °C … 0 °C"


def test_format_image_link_basic(tmp_path):
    # Создаем файл изображения внутри output_dir
    output_dir = tmp_path
    img_path = output_dir / "img.jpg"
    img_path.write_bytes(b"binary")

    # Абсолютный путь внутри output_dir -> относительный 'img.jpg'
    result = format_image_link(str(img_path), "Alpha", str(output_dir))
    assert result == f"![Alpha]({img_path.name})"

    # Список путей: берется первый элемент
    result2 = format_image_link([str(img_path), str(output_dir / "img2.jpg")], "Alpha", str(output_dir))
    assert result2 == f"![Alpha]({img_path.name})"


@pytest.mark.parametrize("val", [None, "", [], [""], 123])
def test_format_image_link_invalid(val, tmp_path):
    assert format_image_link(val, "Name", str(tmp_path)) == ""


def test_format_similars_with_links(tmp_path):
    # Подготовим структуру: файл структуры внутри output_dir/service
    output_dir = tmp_path
    service_dir = output_dir / "service"
    service_dir.mkdir(parents=True)
    struct_file = service_dir / "S1.yaml"
    struct_file.write_text("name: S1\n")

    # Стаб с методом get_path_by_name
    generator_stub = SimpleNamespace(get_path_by_name=lambda name: str(struct_file) if name == "S1" else None)

    res = format_similars_with_links(["S1", "Missing", None, "  "], generator_stub, str(output_dir))
    # Ссылка на найденную структуру с относительным путем и просто текст для отсутствующей
    assert "[S1](service/S1.yaml)" in res
    assert "Missing" in res


def test_format_similars_with_links_non_list_returns_str():
    generator_stub = SimpleNamespace(get_path_by_name=lambda _name: None)
    assert format_similars_with_links("S1", generator_stub, ".") == "S1"


def test_formatters_relative_path_fallbacks(tmp_path):
    # Подготовим файлы в tmp_path, а output_dir сделаем отдельной директорией
    svc_dir = tmp_path / "svc"
    svc_dir.mkdir(parents=True)
    struct_file = svc_dir / "S2.yaml"
    struct_file.write_text("name: S2\n")

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    generator_stub = SimpleNamespace(get_path_by_name=lambda name: str(struct_file) if name == "S2" else None)

    # format_similars_with_links -> путь не является поддиректорией output_dir, должен сработать relpath(...)
    txt = format_similars_with_links(["S2"], generator_stub, str(out_dir))
    assert "](" in txt  # есть ссылка
    assert ")" in txt

    # format_image_link -> тот же случай с разными директориями
    link = format_image_link(str(struct_file), "S2", str(out_dir))
    assert link.startswith("![S2](")
    assert ")" in link
