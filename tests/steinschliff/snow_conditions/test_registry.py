from steinschliff.snow_conditions import get_name_ru, get_valid_keys, normalize_condition_input


def test_get_valid_keys_contains_known_keys():
    keys = get_valid_keys()
    assert "red" in keys
    assert "blue" in keys


def test_get_name_ru_returns_value_for_known_key():
    # В репозитории есть snow_conditions/blue.yaml
    assert get_name_ru("blue")


def test_normalize_condition_input_supports_ru_color_names():
    assert normalize_condition_input("Зелёный") == "green"
    assert normalize_condition_input("желтый") == "yellow"


def test_normalize_condition_input_falls_back_to_lower():
    assert normalize_condition_input("UnknownValue") == "unknownvalue"
