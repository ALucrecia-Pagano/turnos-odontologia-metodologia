from uuid import UUID

from pydantic import ValidationError
import pytest

from app.api.schemas import (
    ChairInput,
    ChairResponse,
    PatientInput,
    PatientResponse,
    ProfessionalInput,
    ProfessionalResponse,
    ServiceInput,
    ServiceResponse,
)


def test_professional_input_schema() -> None:
    # camelCase parsing
    inp = ProfessionalInput.model_validate({"fullName": "Dra. Test", "licenseNumber": "MN-123"})
    assert inp.full_name == "Dra. Test"
    assert inp.license_number == "MN-123"

    # optional licenseNumber
    inp2 = ProfessionalInput.model_validate({"fullName": "Dra. Test"})
    assert inp2.license_number is None

    # extra forbid
    with pytest.raises(ValidationError):
        ProfessionalInput.model_validate({"fullName": "Dra. Test", "extra": "forbidden"})


def test_chair_input_schema() -> None:
    inp = ChairInput.model_validate({"name": "Sillón 1"})
    assert inp.name == "Sillón 1"

    with pytest.raises(ValidationError):
        ChairInput.model_validate({"name": "Sillón 1", "extra": "forbidden"})


def test_service_input_schema() -> None:
    inp = ServiceInput.model_validate({"name": "Consulta", "defaultDurationMin": 30})
    assert inp.name == "Consulta"
    assert inp.default_duration_min == 30

    with pytest.raises(ValidationError):
        ServiceInput.model_validate({"name": "Consulta", "defaultDurationMin": 30, "extra": "forbidden"})


def test_patient_input_schema() -> None:
    inp = PatientInput.model_validate({
        "fullName": "Juan Perez",
        "dni": "30111222",
        "phone": "11223344",
        "healthInsurance": "OSDE",
    })
    assert inp.full_name == "Juan Perez"
    assert inp.dni == "30111222"
    assert inp.phone == "11223344"
    assert inp.health_insurance == "OSDE"

    with pytest.raises(ValidationError):
        PatientInput.model_validate({"fullName": "Juan Perez", "dni": "30111222", "extra": "forbidden"})


def test_catalog_output_schemas_serialize_camelcase() -> None:
    uid = UUID("00000000-0000-0000-0000-000000000001")

    p_resp = ProfessionalResponse(
        id=uid,
        full_name="Dra. Test",
        active=True,
        license_number="MN-123",
    )
    p_dict = p_resp.model_dump(by_alias=True, mode="json")
    assert p_dict["fullName"] == "Dra. Test"
    assert p_dict["licenseNumber"] == "MN-123"
    assert "full_name" not in p_dict

    c_resp = ChairResponse(id=uid, name="Sillón 1", active=True)
    c_dict = c_resp.model_dump(by_alias=True, mode="json")
    assert c_dict["name"] == "Sillón 1"
    assert c_dict["active"] is True

    s_resp = ServiceResponse(
        id=uid,
        name="Limpieza",
        default_duration_min=45,
        active=True,
    )
    s_dict = s_resp.model_dump(by_alias=True, mode="json")
    assert s_dict["defaultDurationMin"] == 45
    assert "default_duration_min" not in s_dict

    pat_resp = PatientResponse(
        id=uid,
        full_name="Juan Perez",
        dni="30111222",
        phone="11223344",
        health_insurance="OSDE",
    )
    pat_dict = pat_resp.model_dump(by_alias=True, mode="json")
    assert pat_dict["fullName"] == "Juan Perez"
    assert pat_dict["healthInsurance"] == "OSDE"
    assert "full_name" not in pat_dict
    assert "health_insurance" not in pat_dict
