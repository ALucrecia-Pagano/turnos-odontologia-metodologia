"""Altas puras: componen reglas y no persisten las entidades aceptadas."""

from collections.abc import Sequence
from dataclasses import replace

from app.domain.catalog.result import CatalogResult, Ok
from app.domain.model import Chair, Patient, Professional, Service
from app.domain.rules.catalog_names import check_duplicate_name, check_name
from app.domain.rules.dni import check_dni, check_duplicate_dni, normalize_dni
from app.domain.rules.duration import check_duration
from app.domain.violations import Rejected


def create_professional(candidate: Professional) -> CatalogResult[Professional]:
    """Acepta un profesional candidato sin modificar sus valores."""
    violations = check_name(candidate.full_name, "del profesional")
    return Rejected(tuple(violations)) if violations else Ok(candidate)


def create_chair(candidate: Chair, existing: Sequence[Chair]) -> CatalogResult[Chair]:
    """Acepta un sillón sin modificar la colección recibida."""
    violations = check_name(candidate.name, "del sillón")
    if not violations:
        violations += check_duplicate_name(
            candidate.name, [item.name for item in existing], "un sillón"
        )
    return Rejected(tuple(violations)) if violations else Ok(candidate)


def create_service(candidate: Service, existing: Sequence[Service]) -> CatalogResult[Service]:
    """Acepta una prestación candidata sin modificar sus datos."""
    violations = check_name(candidate.name, "de la prestación")
    if not violations:
        violations += check_duplicate_name(
            candidate.name, [item.name for item in existing], "una prestación"
        )
    violations += check_duration(candidate.default_duration_min, subject="de la prestación")
    return Rejected(tuple(violations)) if violations else Ok(candidate)


def create_patient(candidate: Patient, existing: Sequence[Patient]) -> CatalogResult[Patient]:
    """Devuelve copia aceptada con DNI normalizado, sin modificar la candidata."""
    violations = check_name(candidate.full_name, "del paciente")
    dni_violations = check_dni(candidate.dni)
    violations += dni_violations
    if not dni_violations:
        violations += check_duplicate_dni(candidate.dni, [item.dni for item in existing])
    if violations:
        return Rejected(tuple(violations))
    return Ok(replace(candidate, dni=normalize_dni(candidate.dni)))
