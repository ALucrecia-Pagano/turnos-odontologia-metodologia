"""Datos exclusivamente ficticios, reutilizables por tests y futuro seed.

No accede a persistencia ni ejecuta un seed. El dominio no importa este módulo.
"""

from uuid import UUID

from app.domain.model import Chair, Patient, Professional, Service

PROFESSIONALS: tuple[Professional, ...] = (
    Professional(UUID("00000000-0000-0000-0000-000000000001"), "Dra. Laura Quiroga", True),
    Professional(UUID("00000000-0000-0000-0000-000000000002"), "Dr. Martín Sosa", True),
    Professional(UUID("00000000-0000-0000-0000-000000000003"), "Dra. Paula Benítez", True),
)
CHAIRS: tuple[Chair, ...] = (
    Chair(UUID("00000000-0000-0000-0000-0000000000b1"), "Sillón 1", True),
    Chair(UUID("00000000-0000-0000-0000-0000000000b2"), "Sillón 2", True),
    Chair(UUID("00000000-0000-0000-0000-0000000000b3"), "Sillón 3", True),
)
SERVICES: tuple[Service, ...] = (
    Service(UUID("00000000-0000-0000-0000-0000000000d1"), "Limpieza", 45),
    Service(UUID("00000000-0000-0000-0000-0000000000d2"), "Extracción", 60),
    Service(UUID("00000000-0000-0000-0000-0000000000d3"), "Restauración", 60),
    Service(UUID("00000000-0000-0000-0000-0000000000d4"), "Control", 30),
    Service(UUID("00000000-0000-0000-0000-0000000000d5"), "Blanqueamiento", 90),
)
PATIENTS: tuple[Patient, ...] = (
    Patient(UUID("00000000-0000-0000-0000-0000000000c1"), "Ana Pérez", "30111222"),
    Patient(UUID("00000000-0000-0000-0000-0000000000c2"), "Bruno Acosta", "28444555"),
    Patient(UUID("00000000-0000-0000-0000-0000000000c3"), "Carla Medina", "27123456"),
    Patient(UUID("00000000-0000-0000-0000-0000000000c4"), "Diego Ríos", "33456789"),
    Patient(UUID("00000000-0000-0000-0000-0000000000c5"), "Eva Molina", "38987654"),
)
