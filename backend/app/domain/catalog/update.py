"""Validaciones puras de edición para catálogos y pacientes.

No accede a I/O, base de datos ni reloj global.
"""

from collections.abc import Sequence
from dataclasses import replace

from app.domain.catalog.result import CatalogResult, Ok
from app.domain.model import Chair, Patient, Professional, Service
from app.domain.rules.catalog_names import check_duplicate_name, check_name
from app.domain.rules.dni import check_dni, check_duplicate_dni, normalize_dni
from app.domain.rules.duration import check_duration
from app.domain.violations import Rejected


def update_professional(candidate: Professional) -> CatalogResult[Professional]:
    """Valida la edición de un profesional. El nombre no es único."""
    violations = check_name(candidate.full_name, "del profesional")
    return Rejected(tuple(violations)) if violations else Ok(candidate)


def update_chair(candidate: Chair, existing: Sequence[Chair]) -> CatalogResult[Chair]:
    """Valida la edición de un sillón excluyendo el propio identificador de duplicados."""
    violations = check_name(candidate.name, "del sillón")
    if not violations:
        other_names = [item.name for item in existing if item.id != candidate.id]
        violations += check_duplicate_name(candidate.name, other_names, "un sillón")
    return Rejected(tuple(violations)) if violations else Ok(candidate)


def update_service(candidate: Service, existing: Sequence[Service]) -> CatalogResult[Service]:
    """Valida la edición de una prestación excluyendo el propio identificador de duplicados."""
    violations = check_name(candidate.name, "de la prestación")
    if not violations:
        other_names = [item.name for item in existing if item.id != candidate.id]
        violations += check_duplicate_name(candidate.name, other_names, "una prestación")
    violations += check_duration(candidate.default_duration_min, subject="de la prestación")
    return Rejected(tuple(violations)) if violations else Ok(candidate)


def update_patient(candidate: Patient, existing: Sequence[Patient]) -> CatalogResult[Patient]:
    """Valida la edición de un paciente excluyendo el propio identificador de duplicados."""
    violations = check_name(candidate.full_name, "del paciente")
    dni_violations = check_dni(candidate.dni)
    violations += dni_violations
    if not dni_violations:
        other_dnis = [item.dni for item in existing if item.id != candidate.id]
        violations += check_duplicate_dni(candidate.dni, other_dnis)
    if violations:
        return Rejected(tuple(violations))
    return Ok(replace(candidate, dni=normalize_dni(candidate.dni)))
