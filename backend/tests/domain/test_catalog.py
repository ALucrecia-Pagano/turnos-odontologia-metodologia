from dataclasses import replace
from uuid import UUID

import pytest

from app.domain.model import Chair, Patient, Professional, Service
from app.domain.violations import Rejected, Violation, ViolationCode
from app.domain.catalog.result import Ok

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
S2 = UUID("00000000-0000-0000-0000-0000000000b2")
SV1 = UUID("00000000-0000-0000-0000-0000000000d1")
SV2 = UUID("00000000-0000-0000-0000-0000000000d2")
PA1 = UUID("00000000-0000-0000-0000-0000000000c1")
PA2 = UUID("00000000-0000-0000-0000-0000000000c2")


def test_catalog_ok_keeps_professional_entity() -> None:
    entity = Professional(P1, "Dra. Laura Quiroga", True)
    assert Ok(entity).entity == entity


def test_catalog_ok_keeps_patient_entity() -> None:
    entity = Patient(PA1, "Ana Pérez", "30111222")
    assert Ok(entity).entity == entity


def test_create_professional_valid() -> None:
    from app.domain.catalog.create import create_professional

    candidate = Professional(P1, "Dra. Laura Quiroga", True)
    assert create_professional(candidate) == Ok(candidate)


def test_create_professional_empty_name() -> None:
    from app.domain.catalog.create import create_professional

    assert create_professional(Professional(P1, "", True)) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del profesional no puede estar vacío."),
    ))


def test_create_professional_blank_name() -> None:
    from app.domain.catalog.create import create_professional

    assert create_professional(Professional(P1, "   ", True)) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del profesional no puede estar vacío."),
    ))


def test_create_professional_repeated_name_allowed() -> None:
    from app.domain.catalog.create import create_professional

    first = Professional(P1, "Dra. Laura Quiroga", True)
    second = Professional(P2, "Dra. Laura Quiroga", True)
    assert create_professional(first) == Ok(first)
    assert create_professional(second) == Ok(second)


def test_create_professional_preserves_original_name() -> None:
    from app.domain.catalog.create import create_professional

    candidate = Professional(P1, "  Dra. Laura  Quiroga  ", True)
    assert create_professional(candidate) == Ok(candidate)


def test_create_chair_valid() -> None:
    from app.domain.catalog.create import create_chair

    candidate = Chair(S1, "Sillón 1", True)
    assert create_chair(candidate, ()) == Ok(candidate)


def test_create_chair_different_preserves_collection() -> None:
    from app.domain.catalog.create import create_chair

    first = Chair(S1, "Sillón 1", True)
    existing = [first]
    candidate = Chair(S2, "Sillón 2", True)
    assert create_chair(candidate, existing) == Ok(Chair(S2, "Sillón 2", True))
    assert existing == [Chair(S1, "Sillón 1", True)]
    assert candidate == Chair(S2, "Sillón 2", True)


def test_create_chair_empty_name() -> None:
    from app.domain.catalog.create import create_chair

    assert create_chair(Chair(S1, "", True), ()) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del sillón no puede estar vacío."),
    ))


@pytest.mark.parametrize("name", ["", "   "], ids=["empty", "blank"])
def test_create_chair_empty_does_not_duplicate(name: str) -> None:
    from app.domain.catalog.create import create_chair

    assert create_chair(Chair(S2, name, True), (Chair(S1, "   ", True),)) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del sillón no puede estar vacío."),
    ))


def test_create_chair_duplicate_exact() -> None:
    from app.domain.catalog.create import create_chair

    assert create_chair(Chair(S2, "Sillón 1", True), (Chair(S1, "Sillón 1", True),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe un sillón con el nombre "Sillón 1".'),
    ))


def test_create_chair_duplicate_case_and_spaces() -> None:
    from app.domain.catalog.create import create_chair

    candidate = Chair(S2, "  SILLÓN   1  ", True)
    assert create_chair(candidate, (Chair(S1, "Sillón 1", True),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe un sillón con el nombre "SILLÓN 1".'),
    ))
    assert candidate.name == "  SILLÓN   1  "


def test_create_chair_accents_distinguish_names() -> None:
    from app.domain.catalog.create import create_chair

    candidate = Chair(S2, "Sillon 1", True)
    assert create_chair(candidate, (Chair(S1, "Sillón 1", True),)) == Ok(candidate)


def test_create_chair_inactive_name_still_unique() -> None:
    from app.domain.catalog.create import create_chair

    assert create_chair(Chair(S2, "Sillón 1", True), (Chair(S1, "Sillón 1", False),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe un sillón con el nombre "Sillón 1".'),
    ))


@pytest.mark.parametrize("reverse", [False, True], ids=["direct", "reverse"])
def test_create_chair_multiple_equivalents_one_violation(reverse: bool) -> None:
    from app.domain.catalog.create import create_chair

    existing = [Chair(S1, "Sillón 1", True), Chair(S2, " SILLÓN  1 ", True)]
    if reverse:
        existing.reverse()
    assert create_chair(Chair(P2, "Sillón 1", True), existing) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe un sillón con el nombre "Sillón 1".'),
    ))


def test_create_service_valid() -> None:
    from app.domain.catalog.create import create_service

    candidate = Service(SV1, "Limpieza", 45)
    assert create_service(candidate, ()) == Ok(Service(SV1, "Limpieza", 45, True))


def test_create_service_empty_name() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "", 45), ()) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre de la prestación no puede estar vacío."),
    ))


@pytest.mark.parametrize("name", ["", "   "], ids=["empty", "blank"])
def test_create_service_empty_does_not_duplicate(name: str) -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV2, name, 45), (Service(SV1, "   ", 45),)) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre de la prestación no puede estar vacío."),
    ))


def test_create_service_duplicate_exact() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV2, "Limpieza", 45), (Service(SV1, "Limpieza", 45),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "Limpieza".'),
    ))


def test_create_service_duplicate_case_and_spaces() -> None:
    from app.domain.catalog.create import create_service

    candidate = Service(SV2, '  Limpieza  ', 45)
    assert create_service(candidate, (Service(SV1, '  LIMPIEZA  ', 45),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "Limpieza".'),
    ))
    assert candidate.name == '  Limpieza  '


def test_create_service_duplicate_internal_spaces() -> None:
    from app.domain.catalog.create import create_service

    candidate = Service(SV2, ' CONTROL   DE  ORTODONCIA ', 45)
    assert create_service(candidate, (Service(SV1, 'Control de ortodoncia', 45),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "CONTROL DE ORTODONCIA".'),
    ))
    assert candidate.name == ' CONTROL   DE  ORTODONCIA '


def test_create_service_accents_distinguish_names() -> None:
    from app.domain.catalog.create import create_service

    candidate = Service(SV2, "Extraccion", 60)
    assert create_service(candidate, (Service(SV1, "Extracción", 60),)) == Ok(candidate)


def test_create_service_inactive_name_still_unique() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV2, "Limpieza", 45), (Service(SV1, "Limpieza", 45, False),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "Limpieza".'),
    ))


@pytest.mark.parametrize("reverse", [False, True], ids=["direct", "reverse"])
def test_create_service_multiple_equivalents_one_violation(reverse: bool) -> None:
    from app.domain.catalog.create import create_service

    existing = [Service(SV1, "Limpieza", 45), Service(SV2, " LIMPIEZA ", 45)]
    if reverse:
        existing.reverse()
    assert create_service(Service(P2, "Limpieza", 45), existing) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "Limpieza".'),
    ))


def test_create_service_duration_7() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", 7), ()) == Rejected((
        Violation(ViolationCode.INVALID_DURATION, 'La duración de la prestación no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos.'),
    ))


def test_create_service_duration_0() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", 0), ()) == Rejected((
        Violation(ViolationCode.INVALID_DURATION, 'La duración de la prestación no es válida (se recibió 0 minutos): debe ser mayor que cero minutos.'),
    ))


def test_create_service_duration_negative_5() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", -5), ()) == Rejected((
        Violation(ViolationCode.INVALID_DURATION, 'La duración de la prestación no es válida (se recibió -5 minutos): debe ser mayor que cero minutos.'),
    ))


def test_create_service_duration_485() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", 485), ()) == Rejected((
        Violation(ViolationCode.INVALID_DURATION, 'La duración de la prestación no es válida (se recibió 485 minutos): no puede superar los 480 minutos.'),
    ))


def test_create_service_duration_487() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", 487), ()) == Rejected((
        Violation(ViolationCode.INVALID_DURATION, 'La duración de la prestación no es válida (se recibió 487 minutos): debe ser múltiplo de 5 minutos y no puede superar los 480 minutos.'),
    ))


def test_create_service_duration_valid_5() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", 5), ()) == Ok(Service(SV1, "Limpieza", 5))


def test_create_service_duration_valid_480() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV1, "Limpieza", 480), ()) == Ok(Service(SV1, "Limpieza", 480))


def test_create_patient_valid_dni_with_dots() -> None:
    from app.domain.catalog.create import create_patient

    candidate = Patient(PA1, "Ana Pérez", "30.111.222")
    existing: list[Patient] = []
    assert create_patient(candidate, existing) == Ok(Patient(PA1, "Ana Pérez", "30111222"))
    assert candidate == Patient(PA1, "Ana Pérez", "30.111.222")
    assert existing == []


def test_create_patient_valid_dni_without_dots() -> None:
    from app.domain.catalog.create import create_patient

    candidate = Patient(PA1, "Ana Pérez", "30111222")
    assert create_patient(candidate, ()) == Ok(Patient(PA1, "Ana Pérez", "30111222", None, None))


def test_create_patient_empty_name() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "", "30111222"), ()) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del paciente no puede estar vacío."),
    ))


def test_create_patient_blank_name() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "   ", "30111222"), ()) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del paciente no puede estar vacío."),
    ))


def test_create_patient_repeated_name_allowed() -> None:
    from app.domain.catalog.create import create_patient

    candidate = Patient(PA2, "Ana Pérez", "30111223")
    assert create_patient(candidate, (Patient(PA1, "Ana Pérez", "30111222"),)) == Ok(candidate)


@pytest.mark.parametrize(
    ("phone", "insurance"), [("interno ficticio", "plan de ejemplo"), ("", "")], ids=["free-text", "empty"]
)
def test_create_patient_preserves_optional_free_text(phone: str, insurance: str) -> None:
    from app.domain.catalog.create import create_patient

    candidate = Patient(PA1, "Ana Pérez", "30111222", phone, insurance)
    assert create_patient(candidate, ()) == Ok(Patient(PA1, "Ana Pérez", "30111222", phone, insurance))


def test_create_patient_invalid_dni_hyphens() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", "30-111-222"), ()) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_invalid_dni_six() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", '111222'), ()) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "111222"): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_invalid_dni_nine() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", '301112222'), ()) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "301112222"): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_invalid_dni_letters() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", '30111A22'), ()) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "30111A22"): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_invalid_dni_empty() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", ''), ()) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió ""): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_invalid_dni_blank() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", '   '), ()) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "   "): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_valid_dni_seven() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", '3.111.222'), ()) == Ok(Patient(PA1, "Ana Pérez", '3111222'))


def test_create_patient_valid_dni_outer_spaces() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", ' 30.111.222 '), ()) == Ok(Patient(PA1, "Ana Pérez", '30111222'))


def test_create_patient_valid_dni_inner_spaces() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "Ana Pérez", '30 111 222'), ()) == Ok(Patient(PA1, "Ana Pérez", '30111222'))


def test_create_patient_duplicate_dni_exact() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA2, "Ana Pérez", "30111222"), (Patient(PA1, "Ana Pérez", "30111222"),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 30.111.222."),
    ))


def test_create_patient_duplicate_dni_candidate_dots() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA2, "Ana Pérez", '30.111.222'), (Patient(PA1, "Ana Pérez", '30111222'),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 30.111.222."),
    ))


def test_create_patient_duplicate_dni_existing_dots() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA2, "Ana Pérez", '30111222'), (Patient(PA1, "Ana Pérez", '30.111.222'),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 30.111.222."),
    ))


def test_create_patient_duplicate_dni_seven() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA2, "Ana Pérez", '3.111.222'), (Patient(PA1, "Ana Pérez", '3111222'),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 3.111.222."),
    ))


@pytest.mark.parametrize("reverse", [False, True], ids=["direct", "reverse"])
def test_create_patient_duplicate_dni_collection_order(reverse: bool) -> None:
    from app.domain.catalog.create import create_patient

    existing = [Patient(PA2, "Ana Pérez", "30111223"), Patient(PA1, "Ana Pérez", "30111222")]
    if reverse:
        existing.reverse()
    before = tuple(existing)
    assert create_patient(Patient(P2, "Ana Pérez", "30.111.222"), existing) == Rejected((
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 30.111.222."),
    ))
    assert tuple(existing) == before


def test_create_patient_invalid_dni_does_not_duplicate() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA2, "Ana Pérez", "30-111-222"), (Patient(PA1, "Ana Pérez", "30-111-222"),)) == Rejected((
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_name_and_dni_invalid_together() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA1, "", "30-111-222"), ()) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del paciente no puede estar vacío."),
        Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.'),
    ))


def test_create_patient_empty_name_and_duplicate_dni_ordered() -> None:
    from app.domain.catalog.create import create_patient

    assert create_patient(Patient(PA2, "   ", "30.111.222"), (Patient(PA1, "Ana Pérez", "30111222"),)) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del paciente no puede estar vacío."),
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 30.111.222."),
    ))


def test_create_service_duplicate_and_duration_ordered() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV2, "Limpieza", 487), (Service(SV1, "Limpieza", 45),)) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "Limpieza".'),
        Violation(ViolationCode.INVALID_DURATION, "La duración de la prestación no es válida (se recibió 487 minutos): debe ser múltiplo de 5 minutos y no puede superar los 480 minutos."),
    ))


def test_create_service_empty_name_and_duration_ordered_without_duplicate() -> None:
    from app.domain.catalog.create import create_service

    assert create_service(Service(SV2, "", 0), (Service(SV1, "", 45),)) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre de la prestación no puede estar vacío."),
        Violation(ViolationCode.INVALID_DURATION, "La duración de la prestación no es válida (se recibió 0 minutos): debe ser mayor que cero minutos."),
    ))


def test_catalog_violation_metadata_empty() -> None:
    from app.domain.catalog.create import create_chair, create_patient, create_professional

    result = create_professional(Professional(P1, "", True))
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(ViolationCode.EMPTY_NAME, 'El nombre del profesional no puede estar vacío.'),)
    violation = result.violations[0]
    assert (violation.reference_kind, violation.conflicting_appointment_id, violation.conflicting_block_id, violation.conflicting_interval) == (None, None, None, None)


def test_catalog_violation_metadata_name() -> None:
    from app.domain.catalog.create import create_chair, create_patient, create_professional

    result = create_chair(Chair(S2, "Sillón 1", True), (Chair(S1, "Sillón 1", True),))
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe un sillón con el nombre "Sillón 1".'),)
    violation = result.violations[0]
    assert (violation.reference_kind, violation.conflicting_appointment_id, violation.conflicting_block_id, violation.conflicting_interval) == (None, None, None, None)


def test_catalog_violation_metadata_invalid() -> None:
    from app.domain.catalog.create import create_chair, create_patient, create_professional

    result = create_patient(Patient(PA1, "Ana Pérez", "30-111-222"), ())
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(ViolationCode.INVALID_DNI, 'El DNI no es válido (se recibió "30-111-222"): debe tener 7 u 8 dígitos, con o sin puntos.'),)
    violation = result.violations[0]
    assert (violation.reference_kind, violation.conflicting_appointment_id, violation.conflicting_block_id, violation.conflicting_interval) == (None, None, None, None)


def test_catalog_violation_metadata_dni() -> None:
    from app.domain.catalog.create import create_chair, create_patient, create_professional

    result = create_patient(Patient(PA2, "Ana Pérez", "30111222"), (Patient(PA1, "Ana Pérez", "30111222"),))
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(ViolationCode.DUPLICATE_DNI, 'Ya existe un paciente con el DNI 30.111.222.'),)
    violation = result.violations[0]
    assert (violation.reference_kind, violation.conflicting_appointment_id, violation.conflicting_block_id, violation.conflicting_interval) == (None, None, None, None)


def test_deactivate_professional_returns_copy() -> None:
    from app.domain.catalog.activation import deactivate

    original = Professional(P1, "Dra. Laura Quiroga", True)
    assert deactivate(original) == Professional(P1, "Dra. Laura Quiroga", False)
    assert original == Professional(P1, "Dra. Laura Quiroga", True)


def test_deactivate_chair_returns_copy() -> None:
    from app.domain.catalog.activation import deactivate

    original = Chair(S1, "Sillón 1", True)
    assert deactivate(original) == Chair(S1, "Sillón 1", False)
    assert original == Chair(S1, "Sillón 1", True)


def test_deactivate_service_returns_copy() -> None:
    from app.domain.catalog.activation import deactivate

    original = Service(SV1, "Limpieza", 45, True)
    assert deactivate(original) == Service(SV1, "Limpieza", 45, False)
    assert original == Service(SV1, "Limpieza", 45, True)


def test_reactivate_professional_returns_copy() -> None:
    from app.domain.catalog.activation import reactivate

    original = Professional(P1, "Dra. Laura Quiroga", False)
    assert reactivate(original) == Professional(P1, "Dra. Laura Quiroga", True)
    assert original == Professional(P1, "Dra. Laura Quiroga", False)


def test_reactivate_chair_returns_copy() -> None:
    from app.domain.catalog.activation import reactivate

    original = Chair(S1, "Sillón 1", False)
    assert reactivate(original) == Chair(S1, "Sillón 1", True)
    assert original == Chair(S1, "Sillón 1", False)


def test_reactivate_service_returns_copy() -> None:
    from app.domain.catalog.activation import reactivate

    original = Service(SV1, "Limpieza", 45, False)
    assert reactivate(original) == Service(SV1, "Limpieza", 45, True)
    assert original == Service(SV1, "Limpieza", 45, False)


def test_deactivate_professional_is_idempotent() -> None:
    from app.domain.catalog.activation import deactivate

    original = Professional(P1, "Dra. Laura Quiroga", False)
    assert deactivate(original) == Professional(P1, "Dra. Laura Quiroga", False)
    assert original == Professional(P1, "Dra. Laura Quiroga", False)


def test_deactivate_chair_is_idempotent() -> None:
    from app.domain.catalog.activation import deactivate

    original = Chair(S1, "Sillón 1", False)
    assert deactivate(original) == Chair(S1, "Sillón 1", False)
    assert original == Chair(S1, "Sillón 1", False)


def test_deactivate_service_is_idempotent() -> None:
    from app.domain.catalog.activation import deactivate

    original = Service(SV1, "Limpieza", 45, False)
    assert deactivate(original) == Service(SV1, "Limpieza", 45, False)
    assert original == Service(SV1, "Limpieza", 45, False)


def test_reactivate_professional_is_idempotent() -> None:
    from app.domain.catalog.activation import reactivate

    original = Professional(P1, "Dra. Laura Quiroga", True)
    assert reactivate(original) == Professional(P1, "Dra. Laura Quiroga", True)
    assert original == Professional(P1, "Dra. Laura Quiroga", True)


def test_reactivate_chair_is_idempotent() -> None:
    from app.domain.catalog.activation import reactivate

    original = Chair(S1, "Sillón 1", True)
    assert reactivate(original) == Chair(S1, "Sillón 1", True)
    assert original == Chair(S1, "Sillón 1", True)


def test_reactivate_service_is_idempotent() -> None:
    from app.domain.catalog.activation import reactivate

    original = Service(SV1, "Limpieza", 45, True)
    assert reactivate(original) == Service(SV1, "Limpieza", 45, True)
    assert original == Service(SV1, "Limpieza", 45, True)


def test_demo_working_hours_are_valid_and_have_expected_distribution() -> None:
    from app.demo_data import WORKING_HOURS
    from app.domain.model import WorkingHours
    from app.domain.rules.working_hours import validate_working_hours

    assert len(WORKING_HOURS) == 25
    assert validate_working_hours(WORKING_HOURS) == []
    assert sum(slot.professional_id == P1 for slot in WORKING_HOURS) == 10
    assert sum(
        slot.professional_id == P2
        and slot.start_minute == 540
        and slot.end_minute == 780
        for slot in WORKING_HOURS
    ) == 5
    assert sum(
        slot.professional_id == UUID("00000000-0000-0000-0000-000000000003")
        for slot in WORKING_HOURS
    ) == 10
    assert all(isinstance(slot, WorkingHours) for slot in WORKING_HOURS)
