from app.auth.permissions import (
    PERMISSION_MESSAGES,
    PERMISSIONS,
    Action,
    Resource,
    Scope,
    missing_combinations,
)
from app.domain.model import Role
from tests.auth.rbac_matrix import ALL, DENIED, MATRIX, OWN, ROLES


EXPECTED_SCOPE = {ALL: Scope.ALL, OWN: Scope.OWN}
LITERAL_COMBINATIONS = frozenset(
    (Resource[row.resource], Action[row.action]) for row in MATRIX
)


def test_literal_matrix_has_expected_totals() -> None:
    cells = [row.cell(role) for row in MATRIX for role in ROLES]

    assert len(MATRIX) == 34
    assert len(cells) == 102
    assert sum(cell != DENIED for cell in cells) == 61
    assert sum(cell == DENIED for cell in cells) == 41


def test_permissions_match_literal_matrix() -> None:
    differences: list[str] = []
    for row in MATRIX:
        key = (Resource[row.resource], Action[row.action])
        for role in ROLES:
            expected = EXPECTED_SCOPE.get(row.cell(role))
            actual = PERMISSIONS[key].get(Role(role))
            if actual is not expected:
                differences.append(f"fila {row.number}, {role}: {actual} != {expected}")
        if PERMISSION_MESSAGES[key] != f"No tiene permiso para {row.message}.":
            differences.append(f"fila {row.number}: mensaje {PERMISSION_MESSAGES[key]}")

    assert differences == []
    assert set(PERMISSIONS) == LITERAL_COMBINATIONS


def test_no_combination_is_missing() -> None:
    assert missing_combinations(PERMISSIONS, LITERAL_COMBINATIONS) == frozenset()


def test_missing_combination_is_detected() -> None:
    book = (Resource.APPOINTMENT, Action.CREATE)
    incomplete = {key: value for key, value in PERMISSIONS.items() if key != book}

    assert missing_combinations(incomplete, LITERAL_COMBINATIONS) == frozenset({book})
