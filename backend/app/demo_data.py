"""Datos exclusivamente ficticios, reutilizables por tests y futuro seed.

No accede a persistencia ni ejecuta un seed. El dominio no importa este módulo.
"""

from uuid import UUID

from app.auth.model import AuthenticatedUser
from app.domain.model import Chair, Patient, Professional, Role, Service, WorkingHours

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

# Sin contraseña: el seed la toma de SEED_USER_PASSWORD.
USERS: tuple[AuthenticatedUser, ...] = (
    AuthenticatedUser(
        UUID("00000000-0000-0000-0000-0000000000e1"),
        "administrador",
        "Administración Demo",
        Role.ADMINISTRADOR,
        None,
    ),
    AuthenticatedUser(
        UUID("00000000-0000-0000-0000-0000000000e2"),
        "recepcion",
        "Recepción Demo",
        Role.RECEPCION,
        None,
    ),
    AuthenticatedUser(
        UUID("00000000-0000-0000-0000-0000000000e3"),
        "odontologo",
        "Dra. Laura Quiroga",
        Role.ODONTOLOGO,
        PROFESSIONALS[0].id,
    ),
)

WORKING_HOURS: tuple[WorkingHours, ...] = tuple(
    WorkingHours(professional_id, weekday, start_minute, end_minute)
    for professional_id, morning_only in (
        (PROFESSIONALS[0].id, False),
        (PROFESSIONALS[1].id, True),
        (PROFESSIONALS[2].id, False),
    )
    for weekday in range(1, 6)
    for start_minute, end_minute in ((540, 780),)
    + (() if morning_only else ((900, 1140),))
)
