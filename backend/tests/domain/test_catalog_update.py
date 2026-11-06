from uuid import UUID

from app.domain.catalog.result import Ok
from app.domain.catalog.update import (
    update_chair,
    update_patient,
    update_professional,
    update_service,
)
from app.domain.model import Chair, Patient, Professional, Service
from app.domain.violations import Rejected, Violation, ViolationCode

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
S2 = UUID("00000000-0000-0000-0000-0000000000b2")
SRV1 = UUID("00000000-0000-0000-0000-0000000000c1")
SRV2 = UUID("00000000-0000-0000-0000-0000000000c2")
PAT1 = UUID("00000000-0000-0000-0000-0000000000d1")
PAT2 = UUID("00000000-0000-0000-0000-0000000000d2")


def test_update_professional_valid() -> None:
    candidate = Professional(P1, "Dra. Laura Quiroga Modificada", True)
    assert update_professional(candidate) == Ok(candidate)


def test_update_professional_conserving_own_name() -> None:
    candidate = Professional(P1, "Dra. Laura Quiroga", True)
    assert update_professional(candidate) == Ok(candidate)


def test_update_professional_empty_name() -> None:
    candidate = Professional(P1, "", True)
    assert update_professional(candidate) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del profesional no puede estar vacío."),
    ))


def test_update_chair_valid() -> None:
    existing = [Chair(S1, "Sillón 1", True)]
    candidate = Chair(S1, "Sillón Verde", True)
    assert update_chair(candidate, existing) == Ok(candidate)


def test_update_chair_conserving_own_name() -> None:
    existing = [Chair(S1, "Sillón 1", True), Chair(S2, "Sillón 2", True)]
    candidate = Chair(S1, "Sillón 1", True)
    assert update_chair(candidate, existing) == Ok(candidate)


def test_update_chair_with_name_of_another_chair_rejected() -> None:
    existing = [Chair(S1, "Sillón 1", True), Chair(S2, "Sillón 2", True)]
    candidate = Chair(S2, "Sillón 1", True)
    assert update_chair(candidate, existing) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe un sillón con el nombre "Sillón 1".'),
    ))


def test_update_chair_empty_name() -> None:
    existing = [Chair(S1, "Sillón 1", True)]
    candidate = Chair(S1, "", True)
    assert update_chair(candidate, existing) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del sillón no puede estar vacío."),
    ))


def test_update_service_valid() -> None:
    existing = [Service(SRV1, "Consulta General", 30, True)]
    candidate = Service(SRV1, "Consulta General Ampliada", 45, True)
    assert update_service(candidate, existing) == Ok(candidate)


def test_update_service_conserving_own_name() -> None:
    existing = [
        Service(SRV1, "Consulta General", 30, True),
        Service(SRV2, "Limpieza", 45, True),
    ]
    candidate = Service(SRV1, "Consulta General", 60, True)
    assert update_service(candidate, existing) == Ok(candidate)


def test_update_service_with_name_of_another_service_rejected() -> None:
    existing = [
        Service(SRV1, "Consulta General", 30, True),
        Service(SRV2, "Limpieza", 45, True),
    ]
    candidate = Service(SRV2, "Consulta General", 45, True)
    assert update_service(candidate, existing) == Rejected((
        Violation(ViolationCode.DUPLICATE_NAME, 'Ya existe una prestación con el nombre "Consulta General".'),
    ))


def test_update_service_empty_name() -> None:
    existing = [Service(SRV1, "Consulta General", 30, True)]
    candidate = Service(SRV1, "", 30, True)
    assert update_service(candidate, existing) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre de la prestación no puede estar vacío."),
    ))


def test_update_service_invalid_duration() -> None:
    existing = [Service(SRV1, "Consulta General", 30, True)]
    candidate = Service(SRV1, "Consulta General", 0, True)
    assert update_service(candidate, existing) == Rejected((
        Violation(
            ViolationCode.INVALID_DURATION,
            "La duración de la prestación no es válida (se recibió 0 minutos): debe ser mayor que cero minutos.",
        ),
    ))


def test_update_patient_valid() -> None:
    existing = [Patient(PAT1, "Juan Perez", "12.345.678", "11223344", "OSDE")]
    candidate = Patient(PAT1, "Juan Carlos Perez", "12345678", "11223344", "OSDE")
    assert update_patient(candidate, existing) == Ok(
        Patient(PAT1, "Juan Carlos Perez", "12345678", "11223344", "OSDE")
    )


def test_update_patient_conserving_own_dni() -> None:
    existing = [
        Patient(PAT1, "Juan Perez", "12345678", "11223344", "OSDE"),
        Patient(PAT2, "Maria Lopez", "87654321", "22334455", "Swiss"),
    ]
    candidate = Patient(PAT1, "Juan Perez Modificado", "12.345.678", "99887766", "Particular")
    assert update_patient(candidate, existing) == Ok(
        Patient(PAT1, "Juan Perez Modificado", "12345678", "99887766", "Particular")
    )


def test_update_patient_with_dni_of_another_patient_rejected() -> None:
    existing = [
        Patient(PAT1, "Juan Perez", "12345678", "11223344", "OSDE"),
        Patient(PAT2, "Maria Lopez", "87654321", "22334455", "Swiss"),
    ]
    candidate = Patient(PAT2, "Maria Lopez", "12345678", "22334455", "Swiss")
    assert update_patient(candidate, existing) == Rejected((
        Violation(ViolationCode.DUPLICATE_DNI, "Ya existe un paciente con el DNI 12.345.678."),
    ))


def test_update_patient_empty_name() -> None:
    existing = [Patient(PAT1, "Juan Perez", "12345678", "11223344", "OSDE")]
    candidate = Patient(PAT1, "", "12345678", "11223344", "OSDE")
    assert update_patient(candidate, existing) == Rejected((
        Violation(ViolationCode.EMPTY_NAME, "El nombre del paciente no puede estar vacío."),
    ))


def test_update_patient_invalid_dni() -> None:
    existing = [Patient(PAT1, "Juan Perez", "12345678", "11223344", "OSDE")]
    candidate = Patient(PAT1, "Juan Perez", "123", "11223344", "OSDE")
    assert update_patient(candidate, existing) == Rejected((
        Violation(
            ViolationCode.INVALID_DNI,
            'El DNI no es válido (se recibió "123"): debe tener 7 u 8 dígitos, con o sin puntos.',
        ),
    ))
