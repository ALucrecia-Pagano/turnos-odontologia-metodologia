"""Datos exclusivamente ficticios, reutilizables por tests y futuro seed.

No accede a persistencia ni ejecuta un seed. El dominio no importa este módulo.
"""

from uuid import UUID

from app.domain.model import Chair, Patient, Professional, Service

PROFESSIONALS: tuple[Professional, ...] = (
    Professional(UUID("00000000-0000-0000-0000-000000000001"), "Dra. Laura Quiroga", True),
)
CHAIRS: tuple[Chair, ...] = (
    Chair(UUID("00000000-0000-0000-0000-0000000000b1"), "Sillón 1", True),
)
SERVICES: tuple[Service, ...] = (
    Service(UUID("00000000-0000-0000-0000-0000000000d1"), "Limpieza", 45),
)
PATIENTS: tuple[Patient, ...] = (
    Patient(UUID("00000000-0000-0000-0000-0000000000c1"), "Ana Pérez", "30111222"),
)
