"""Nombre obligatorio y unicidad del catálogo, sin I/O."""

from app.domain.violations import Violation, ViolationCode


def check_name(name: str, subject: str) -> list[Violation]:
    """Informa nombre vacío sin lanzar ni normalizar la entidad."""
    if not name.strip():
        return [
            Violation(ViolationCode.EMPTY_NAME, f"El nombre {subject} no puede estar vacío.")
        ]
    return []


def check_duplicate_name(name: str, existing_names: list[str], subject: str) -> list[Violation]:
    """Una violación por nombre repetido entre todos los existentes recibidos."""
    display_name = " ".join(name.split())
    key = display_name.casefold()
    if any(" ".join(existing.split()).casefold() == key for existing in existing_names):
        return [
            Violation(
                ViolationCode.DUPLICATE_NAME,
                f'Ya existe {subject} con el nombre "{display_name}".',
            )
        ]
    return []
