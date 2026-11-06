from collections.abc import Mapping
import sys

from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.config import Settings, load_settings
from app.db.models import ProfessionalModel
from app.db.session import create_session_factory
from app.demo_data import CHAIRS, PATIENTS, PROFESSIONALS, SERVICES, USERS, WORKING_HOURS
from app.domain.catalog.result import Ok
from app.repositories.catalog import ChairRepository, ProfessionalRepository, ServiceRepository
from app.repositories.patients import PatientRepository
from app.repositories.users import UserRepository
from app.repositories.working_hours import WorkingHoursRepository


_LICENSE_NUMBERS: Mapping[str, str] = {
    "00000000-0000-0000-0000-000000000001": "MP-FIC-001",
    "00000000-0000-0000-0000-000000000002": "MP-FIC-002",
    "00000000-0000-0000-0000-000000000003": "MP-FIC-003",
}


SEED_PASSWORD_MIN_LENGTH = 8


class SeedConfigurationError(Exception):
    """El seed no puede correr con esta configuración. Nunca muestra valores."""


def _validated_seed_password(settings: Settings) -> str:
    if settings.app_env == "production":
        raise SeedConfigurationError(
            "El seed no corre con APP_ENV=production: sus usuarios son ficticios."
        )
    secret = settings.seed_user_password
    password = "" if secret is None else secret.get_secret_value()
    if not password.strip():
        raise SeedConfigurationError("Falta SEED_USER_PASSWORD, o está vacía.")
    if len(password) < SEED_PASSWORD_MIN_LENGTH:
        raise SeedConfigurationError(
            f"SEED_USER_PASSWORD debe tener al menos {SEED_PASSWORD_MIN_LENGTH} caracteres."
        )
    return password


def seed_database(settings: Settings | None = None) -> dict[str, int]:
    configured = settings if settings is not None else load_settings()
    # Antes de abrir la transacción: si no sirve, no se escribe nada.
    password = _validated_seed_password(configured)
    session_factory = create_session_factory(configured)
    with session_factory() as session:
        with session.begin():
            _seed_catalogs(session)
            _seed_patients(session)
            _seed_working_hours(session)
            _seed_users(session, password)
            counts = {
                "professional": len(ProfessionalRepository(session).list()),
                "chair": len(ChairRepository(session).list()),
                "service": len(ServiceRepository(session).list()),
                "patient": len(PatientRepository(session).list()),
                "working_hours": len(WorkingHoursRepository(session).list()),
                "app_user": UserRepository(session).count(),
            }
    return counts


def _seed_catalogs(session: Session) -> None:
    professional_repository = ProfessionalRepository(session)
    for professional in PROFESSIONALS:
        if professional_repository.get_by_id(professional.id) is None:
            result = professional_repository.create(professional)
            if not isinstance(result, Ok):
                raise RuntimeError("Los datos ficticios contienen un profesional inválido.")
            row = session.get(ProfessionalModel, professional.id)
            if row is None:
                raise RuntimeError("El seed no pudo leer el profesional recién creado.")
            row.license_number = _LICENSE_NUMBERS[str(professional.id)]

    chair_repository = ChairRepository(session)
    for chair in CHAIRS:
        if chair_repository.get_by_id(chair.id) is None:
            chair_result = chair_repository.create(chair)
            if not isinstance(chair_result, Ok):
                raise RuntimeError("Los datos ficticios contienen un sillón inválido.")

    service_repository = ServiceRepository(session)
    for service in SERVICES:
        if service_repository.get_by_id(service.id) is None:
            service_result = service_repository.create(service)
            if not isinstance(service_result, Ok):
                raise RuntimeError("Los datos ficticios contienen una prestación inválida.")


def _seed_patients(session: Session) -> None:
    repository = PatientRepository(session)
    for patient in PATIENTS:
        if repository.get_by_id(patient.id) is None:
            patient_result = repository.create(patient)
            if not isinstance(patient_result, Ok):
                raise RuntimeError("Los datos ficticios contienen un paciente inválido.")


def _seed_working_hours(session: Session) -> int:
    repository = WorkingHoursRepository(session)
    inserted = 0
    for professional in PROFESSIONALS:
        if repository.list_by_professional(professional.id):
            continue
        slots = tuple(
            slot for slot in WORKING_HOURS if slot.professional_id == professional.id
        )
        result = repository.replace_for_professional(professional.id, slots)
        if not isinstance(result, Ok):
            raise RuntimeError("Los datos ficticios contienen un horario inválido.")
        inserted += len(slots)
    return inserted


def _seed_users(session: Session, password: str) -> None:
    repository = UserRepository(session)
    for user in USERS:
        if repository.get_by_id(user.id) is None:
            repository.create(user, hash_password(password))


def main() -> int:
    try:
        counts = seed_database()
    except SeedConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 1
    for table, count in counts.items():
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
