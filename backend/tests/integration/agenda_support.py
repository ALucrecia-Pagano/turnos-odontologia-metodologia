"""Datos de apoyo para los tests de la agenda (C-24): solo datos ficticios."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.db.models import (
    AppointmentModel,
    BlockModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
)

MINE = {UUID(int=n) for n in range(8001, 8020)}


def base_monday() -> datetime:
    """Lunes lejano (relativo a hoy) para no mezclarse con datos de otros tests."""
    now = datetime.now(timezone.utc)
    base = now + timedelta(days=3650)
    monday = base + timedelta(days=(0 - base.weekday()) % 7)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


@dataclass(frozen=True)
class Seed:
    session: Session
    prof_a: UUID
    prof_b: UUID
    chair_a: UUID
    chair_b: UUID
    patient: UUID
    service: UUID


def seed_catalog(connection: Connection) -> Seed:
    session = Session(bind=connection)
    prof_a, prof_b = UUID(int=7001), UUID(int=7002)
    chair_a, chair_b = UUID(int=7011), UUID(int=7012)
    patient, service = UUID(int=7021), UUID(int=7031)
    session.add_all(
        [
            ProfessionalModel(id=prof_a, full_name="Dra. Agenda Uno", active=True),
            ProfessionalModel(id=prof_b, full_name="Dr. Agenda Dos", active=False),
            ChairModel(id=chair_a, name="Sillón Agenda A", name_normalized="sillon agenda a", active=True),
            ChairModel(id=chair_b, name="Sillón Agenda B", name_normalized="sillon agenda b", active=False),
            PatientModel(id=patient, full_name="Paciente Agenda Ficticio", dni="90000001"),
            ServiceModel(
                id=service,
                name="Servicio Agenda",
                name_normalized="servicio agenda",
                default_duration_min=30,
                active=True,
            ),
        ]
    )
    session.flush()
    return Seed(session, prof_a, prof_b, chair_a, chair_b, patient, service)


def add_appointment(
    seed: Seed,
    ident: int,
    start: datetime,
    minutes: int,
    professional: UUID,
    chair: UUID,
    status: str = "reservado",
) -> UUID:
    identifier = UUID(int=ident)
    seed.session.add(
        AppointmentModel(
            id=identifier,
            patient_id=seed.patient,
            professional_id=professional,
            chair_id=chair,
            service_id=seed.service,
            start_at=start,
            end_at=start + timedelta(minutes=minutes),
            status=status,
            created_at=start,
            updated_at=start,
        )
    )
    seed.session.flush()
    return identifier


MINE = {UUID(int=n) for n in range(8001, 8020)}


def add_block(seed: Seed, ident: int, start: datetime, end: datetime, professional: UUID) -> UUID:
    identifier = UUID(int=ident)
    seed.session.add(
        BlockModel(
            id=identifier,
            professional_id=professional,
            start_at=start,
            end_at=end,
            reason=f"Motivo {ident}",
        )
    )
    seed.session.flush()
    return identifier
