"""Validez y unicidad de DNI recibidos, sin consultar persistencia."""

from app.domain.violations import Violation, ViolationCode


def normalize_dni(dni: str) -> str:
    """Quita únicamente puntos y espacios del DNI recibido."""
    return dni.replace(".", "").replace(" ", "")


def check_dni(dni: str) -> list[Violation]:
    """Una violación si no quedan siete u ocho dígitos; conserva texto recibido."""
    digits = normalize_dni(dni)
    if not digits.isdigit() or len(digits) not in (7, 8):
        return [
            Violation(
                ViolationCode.INVALID_DNI,
                f'El DNI no es válido (se recibió "{dni}"): '
                "debe tener 7 u 8 dígitos, con o sin puntos.",
            )
        ]
    return []


def check_duplicate_dni(dni: str, existing_dnis: list[str]) -> list[Violation]:
    """Una violación por DNI válido repetido, presentado con puntos de miles."""
    digits = normalize_dni(dni)
    if any(normalize_dni(existing) == digits for existing in existing_dnis):
        shown = f"{digits[:-6]}.{digits[-6:-3]}.{digits[-3:]}"
        return [
            Violation(
                ViolationCode.DUPLICATE_DNI,
                f"Ya existe un paciente con el DNI {shown}.",
            )
        ]
    return []
