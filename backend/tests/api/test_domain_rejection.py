import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.api.errors import DomainRejectedError
from app.config import Settings
from app.domain.violations import Rejected, Violation, ViolationCode
from app.main import create_app


@pytest.mark.parametrize(
    "code,expected_status",
    [
        (ViolationCode.PROFESSIONAL_OVERLAP, 409),
        (ViolationCode.CHAIR_OVERLAP, 409),
        (ViolationCode.OUTSIDE_WORKING_HOURS, 409),
        (ViolationCode.BLOCKED_TIME, 409),
        (ViolationCode.DUPLICATE_DNI, 409),
        (ViolationCode.DUPLICATE_NAME, 409),
        (ViolationCode.UNKNOWN_REFERENCE, 422),
        (ViolationCode.INACTIVE_REFERENCE, 422),
        (ViolationCode.INVALID_DURATION, 422),
        (ViolationCode.INVALID_START_TIME, 422),
        (ViolationCode.CROSSES_MIDNIGHT, 422),
        (ViolationCode.IN_THE_PAST, 422),
        (ViolationCode.INVALID_WORKING_HOURS, 422),
        (ViolationCode.OVERLAPPING_WORKING_HOURS, 422),
        (ViolationCode.INVALID_BLOCK, 422),
        (ViolationCode.INVALID_DNI, 422),
        (ViolationCode.EMPTY_NAME, 422),
        (ViolationCode.STATUS_CHANGE_TOO_EARLY, 422),
        (ViolationCode.INVALID_TRANSITION, 422),
        (ViolationCode.FORBIDDEN_OPERATION, 403),
    ],
)
def test_violation_code_maps_to_status(
    api_settings: Settings,
    code: ViolationCode,
    expected_status: int,
) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.get("/test-rejection")
    def trigger_rejection() -> None:
        raise DomainRejectedError(
            Rejected(violations=(Violation(code=code, message=f"Mensaje para {code.value}"),))
        )

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/test-rejection")
    assert response.status_code == expected_status
    assert response.json()["violations"][0]["code"] == code.value


def test_mixed_rejection_keeps_all_violations_in_order(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    v1 = Violation(code=ViolationCode.EMPTY_NAME, message="Nombre vacío")
    v2 = Violation(code=ViolationCode.DUPLICATE_DNI, message="DNI duplicado")

    @router.get("/test-mixed")
    def trigger_mixed() -> None:
        raise DomainRejectedError(Rejected(violations=(v1, v2)))

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/test-mixed")
    assert response.status_code == 422
    codes = [item["code"] for item in response.json()["violations"]]
    assert codes == ["EMPTY_NAME", "DUPLICATE_DNI"]
