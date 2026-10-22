"""Regla de referencias existentes y activas (RN-AG-11).

El llamador resuelve cada referencia y le pasa al dominio la entidad o `None`. El
paciente solo puede no existir; el profesional, el sillon y la prestacion tambien
pueden estar inactivos.
"""

from uuid import UUID

from app.domain.model import (
    AppointmentReferences,
    Chair,
    NewAppointmentRequest,
    Patient,
    Professional,
    Service,
)
from app.domain.violations import ReferenceKind, Violation, ViolationCode

_ARTICLE_AND_NOUN: dict[ReferenceKind, tuple[str, str, str]] = {
    # tipo -> (sustantivo con articulo, "indicado/a", "inactivo/a")
    ReferenceKind.PATIENT: ("El paciente", "indicado", "inactivo"),
    ReferenceKind.PROFESSIONAL: ("El profesional", "indicado", "inactivo"),
    ReferenceKind.CHAIR: ("El sillón", "indicado", "inactivo"),
    ReferenceKind.SERVICE: ("La prestación", "indicada", "inactiva"),
}


def _check_reference(
    kind: ReferenceKind, reference_id: UUID, entity: Patient | Professional | Chair | Service | None
) -> list[Violation]:
    """Violaciones de una sola referencia: inexistente (`None`) o inactiva."""
    noun, indicated, inactive = _ARTICLE_AND_NOUN[kind]
    if entity is None:
        return [
            Violation(
                code=ViolationCode.UNKNOWN_REFERENCE,
                message=f"{noun} {indicated} no existe (id {reference_id}).",
                reference_kind=kind,
            )
        ]
    if isinstance(entity, (Professional, Chair, Service)) and not entity.active:
        return [
            Violation(
                code=ViolationCode.INACTIVE_REFERENCE,
                message=f"{noun} {indicated} está {inactive} (id {reference_id}).",
                reference_kind=kind,
            )
        ]
    return []


def check_references(
    request: NewAppointmentRequest, references: AppointmentReferences
) -> list[Violation]:
    """Devuelve las violaciones de referencias del pedido (RN-AG-11).

    Args:
        request: Pedido de turno; aporta el id de cada referencia para el mensaje.
        references: Entidades resueltas por el llamador, o `None` si no existen.

    Returns:
        Una violacion por cada referencia que falla, en el orden paciente, profesional,
        sillon y prestacion: `UNKNOWN_REFERENCE` si no existe, `INACTIVE_REFERENCE` si
        esta inactiva. Lista vacia si todas existen y estan activas.
    """
    return (
        _check_reference(ReferenceKind.PATIENT, request.patient_id, references.patient)
        + _check_reference(ReferenceKind.PROFESSIONAL, request.professional_id, references.professional)
        + _check_reference(ReferenceKind.CHAIR, request.chair_id, references.chair)
        + _check_reference(ReferenceKind.SERVICE, request.service_id, references.service)
    )
