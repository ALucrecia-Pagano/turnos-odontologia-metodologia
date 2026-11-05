from collections.abc import Sequence
from typing import get_args, get_type_hints


def test_repository_contracts_use_domain_types() -> None:
    from app.domain.model import Chair, Patient, Professional, Service
    from app.repositories.contracts import (
        ChairRepository,
        PatientRepository,
        ProfessionalRepository,
        ServiceRepository,
    )

    assert get_args(get_args(get_type_hints(ProfessionalRepository.create)["return"])[0])[0] is Professional
    assert get_args(get_args(get_type_hints(ChairRepository.create)["return"])[0])[0] is Chair
    assert get_args(get_args(get_type_hints(ServiceRepository.create)["return"])[0])[0] is Service
    assert get_args(get_args(get_type_hints(PatientRepository.create)["return"])[0])[0] is Patient


def test_availability_repository_contracts_use_domain_types() -> None:
    from app.domain.model import Appointment, Block, WorkingHours
    from app.repositories.contracts import (
        AppointmentReader,
        BlockRepository,
        WorkingHoursRepository,
    )

    working_replace = get_type_hints(WorkingHoursRepository.replace_for_professional)
    assert get_args(get_args(working_replace["return"])[0])[0] == tuple[WorkingHours, ...]
    block_create = get_type_hints(BlockRepository.create)
    assert get_args(get_args(block_create["return"])[0])[0] is Block
    affected = get_type_hints(BlockRepository.list_affected_appointments)
    assert affected["return"] == tuple[Appointment, ...]
    reader = get_type_hints(AppointmentReader.list_for_professional_in_range)
    assert reader["return"] == Sequence[Appointment]


def test_appointment_repository_contracts_use_domain_types() -> None:
    from app.domain.model import Appointment, AppointmentStatusChange
    from app.repositories.contracts import (
        AppointmentReader,
        AppointmentRepository,
        AppointmentStatusChangeRepository,
    )

    get_hints = get_type_hints(AppointmentRepository.get_by_id)
    assert get_hints["return"] == Appointment | None

    prof_hints = get_type_hints(AppointmentRepository.list_for_professional_in_range)
    assert prof_hints["return"] == Sequence[Appointment]

    chair_hints = get_type_hints(AppointmentRepository.list_for_chair_in_range)
    assert chair_hints["return"] == Sequence[Appointment]

    history_hints = get_type_hints(AppointmentStatusChangeRepository.list_by_appointment_id)
    assert history_hints["return"] == Sequence[AppointmentStatusChange]
