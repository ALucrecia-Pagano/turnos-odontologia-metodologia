from pathlib import Path

from app.domain.violations import Violation, ViolationCode
from app.api.errors import VIOLATION_STATUS_MAP, status_for, unclassified_codes


def test_all_violation_codes_are_classified() -> None:
    assert unclassified_codes(VIOLATION_STATUS_MAP) == set()


def test_unclassified_code_is_detected() -> None:
    partial_map: dict[ViolationCode, int] = {
        code: status
        for code, status in VIOLATION_STATUS_MAP.items()
        if code != ViolationCode.CHAIR_OVERLAP
    }
    assert unclassified_codes(partial_map) == {ViolationCode.CHAIR_OVERLAP}


def test_mixed_codes_use_precedence() -> None:
    v1 = Violation(code=ViolationCode.EMPTY_NAME, message="Nombre vacío")
    v2 = Violation(code=ViolationCode.DUPLICATE_DNI, message="DNI duplicado")
    assert status_for([v1, v2]) == 422

    v3 = Violation(code=ViolationCode.DUPLICATE_NAME, message="Nombre duplicado")
    v4 = Violation(code=ViolationCode.INVALID_DURATION, message="Duración inválida")
    assert status_for([v3, v4]) == 422

    v5 = Violation(code=ViolationCode.IN_THE_PAST, message="En el pasado")
    v6 = Violation(code=ViolationCode.FORBIDDEN_OPERATION, message="Operación prohibida")
    assert status_for([v5, v6]) == 403


def test_kb_07_lists_all_violation_codes() -> None:
    kb_path = Path(__file__).parents[3] / "knowledge-base" / "07_flujos_principales.md"
    content = kb_path.read_text(encoding="utf-8")
    for code in ViolationCode:
        assert code.value in content

