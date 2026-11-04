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
