import pytest

from steinschliff.catalog import filter_services_by_condition, select_services
from steinschliff.models import ServiceMetadata, StructureInfo


def test_select_services_accepts_directory_key():
    services = {"svc": [StructureInfo(name="S", file_path="x")]}
    meta = {"svc": ServiceMetadata(name="Service Visible")}
    selected = select_services(services=services, service_metadata=meta, service_filter="svc")
    assert list(selected.keys()) == ["svc"]


def test_select_services_accepts_visible_name_case_insensitive():
    services = {"svc": [StructureInfo(name="S", file_path="x")]}
    meta = {"svc": ServiceMetadata(name="Service Visible")}
    selected = select_services(services=services, service_metadata=meta, service_filter="service visible")
    assert list(selected.keys()) == ["svc"]


def test_select_services_raises_for_unknown():
    services = {"svc": [StructureInfo(name="S", file_path="x")]}
    meta = {"svc": ServiceMetadata(name="Service Visible")}
    with pytest.raises(ValueError, match="не найден"):
        select_services(services=services, service_metadata=meta, service_filter="nope")


def test_select_services_returns_all_for_blank_filter():
    services = {"svc": [StructureInfo(name="S", file_path="x")]}
    meta = {"svc": ServiceMetadata(name="Service Visible")}
    selected = select_services(services=services, service_metadata=meta, service_filter="   ")
    assert list(selected.keys()) == ["svc"]


def test_filter_services_by_condition_filters_items():
    services = {
        "svc": [
            StructureInfo(name="A", condition="blue", file_path="a"),
            StructureInfo(name="B", condition="red", file_path="b"),
        ]
    }
    filtered = filter_services_by_condition(services=services, condition_key="blue")
    assert list(filtered.keys()) == ["svc"]
    assert [s.name for s in filtered["svc"]] == ["A"]


def test_filter_services_by_condition_returns_all_for_blank_key():
    services = {"svc": [StructureInfo(name="A", condition="blue", file_path="a")]}
    filtered = filter_services_by_condition(services=services, condition_key="  ")
    assert list(filtered.keys()) == ["svc"]
