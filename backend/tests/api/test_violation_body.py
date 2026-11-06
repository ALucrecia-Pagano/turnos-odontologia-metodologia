from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.api.errors import DomainRejectedError
from app.config import Settings
from app.domain.intervals import Interval
from app.domain.violations import ReferenceKind, Rejected, Violation, ViolationCode
from app.main import create_app


def test_overlap_body(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    v = Violation(
        code=ViolationCode.PROFESSIONAL_OVERLAP,
        message="La Dra. Laura Quiroga ya tiene un turno",
        conflicting_appointment_id=UUID("00000000-0000-0000-0000-00000000a1b2"),
        conflicting_interval=Interval(
            start=datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            end=datetime(2026, 10, 20, 13, 30, tzinfo=timezone.utc),
        ),
    )

    @router.get("/overlap")
    def overlap_route() -> None:
        raise DomainRejectedError(Rejected(violations=(v,)))

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/overlap")
    assert response.status_code == 409
    data = response.json()
    item = data["violations"][0]
    assert set(item.keys()) == {"code", "message", "conflictingAppointmentId", "conflictingInterval"}
    assert item["conflictingAppointmentId"] == "00000000-0000-0000-0000-00000000a1b2"
    assert item["conflictingInterval"] == {
        "startAt": "2026-10-20T13:00:00Z",
        "endAt": "2026-10-20T13:30:00Z",
    }


def test_blocked_time_body(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    v = Violation(
        code=ViolationCode.BLOCKED_TIME,
        message="Horario bloqueado por mantenimiento",
        conflicting_block_id=UUID("00000000-0000-0000-0000-00000000b1c2"),
        conflicting_interval=Interval(
            start=datetime(2026, 10, 20, 14, 0, tzinfo=timezone.utc),
            end=datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc),
        ),
    )

    @router.get("/blocked")
    def blocked_route() -> None:
        raise DomainRejectedError(Rejected(violations=(v,)))

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/blocked")
    assert response.status_code == 409
    data = response.json()
    item = data["violations"][0]
    assert set(item.keys()) == {"code", "message", "conflictingBlockId", "conflictingInterval"}
    assert item["conflictingBlockId"] == "00000000-0000-0000-0000-00000000b1c2"
    assert item["conflictingInterval"] == {
        "startAt": "2026-10-20T14:00:00Z",
        "endAt": "2026-10-20T15:00:00Z",
    }


def test_reference_body(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    v = Violation(
        code=ViolationCode.UNKNOWN_REFERENCE,
        message="Profesional desconocido",
        reference_kind=ReferenceKind.PROFESSIONAL,
    )

    @router.get("/ref")
    def ref_route() -> None:
        raise DomainRejectedError(Rejected(violations=(v,)))

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/ref")
    assert response.status_code == 422
    data = response.json()
    item = data["violations"][0]
    assert set(item.keys()) == {"code", "message", "referenceKind"}
    assert item["referenceKind"] == "PROFESSIONAL"


def test_violation_without_extras_body(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    v = Violation(
        code=ViolationCode.EMPTY_NAME,
        message="El nombre no puede estar vacío",
    )

    @router.get("/simple")
    def simple_route() -> None:
        raise DomainRejectedError(Rejected(violations=(v,)))

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/simple")
    assert response.status_code == 422
    data = response.json()
    item = data["violations"][0]
    assert set(item.keys()) == {"code", "message"}
    assert item["code"] == "EMPTY_NAME"
    assert item["message"] == "El nombre no puede estar vacío"

