from uuid import UUID

import pytest

from app.api.deps import Permission, ensure_own_professional
from app.api.errors import DomainRejectedError
from app.auth.permissions import Action, Resource, Scope
from app.domain.model import Actor, Role
from app.domain.violations import ViolationCode

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
U_ODONTO = UUID("00000000-0000-0000-0000-000000000011")
U_RECEP = UUID("00000000-0000-0000-0000-000000000012")
U_ADMIN = UUID("00000000-0000-0000-0000-000000000013")


def test_odontologist_over_own_professional_passes() -> None:
    actor = Actor(user_id=U_ODONTO, role=Role.ODONTOLOGO, professional_id=P1)
    permission = Permission(actor, Scope.OWN, Resource.WORKING_HOURS, Action.READ)

    # No debe lanzar
    ensure_own_professional(permission, P1)


def test_odontologist_over_other_professional_raises_403_with_cell_message() -> None:
    actor = Actor(user_id=U_ODONTO, role=Role.ODONTOLOGO, professional_id=P1)

    # 1. Celda (WORKING_HOURS, READ) -> "No tiene permiso para leer horarios."
    perm_read_hours = Permission(actor, Scope.OWN, Resource.WORKING_HOURS, Action.READ)
    with pytest.raises(DomainRejectedError) as exc_read:
        ensure_own_professional(perm_read_hours, P2)

    violations = exc_read.value.rejected.violations
    assert len(violations) == 1
    assert violations[0].code == ViolationCode.FORBIDDEN_OPERATION
    assert violations[0].message == "No tiene permiso para leer horarios."

    # 2. Celda (BLOCK, READ) -> "No tiene permiso para leer bloqueos."
    perm_read_blocks = Permission(actor, Scope.OWN, Resource.BLOCK, Action.READ)
    with pytest.raises(DomainRejectedError) as exc_blocks:
        ensure_own_professional(perm_read_blocks, P2)

    violations_blocks = exc_blocks.value.rejected.violations
    assert violations_blocks[0].code == ViolationCode.FORBIDDEN_OPERATION
    assert violations_blocks[0].message == "No tiene permiso para leer bloqueos."

    # 3. Celda (BLOCK, CREATE) -> "No tiene permiso para crear bloqueos."
    perm_create_block = Permission(actor, Scope.OWN, Resource.BLOCK, Action.CREATE)
    with pytest.raises(DomainRejectedError) as exc_create:
        ensure_own_professional(perm_create_block, P2)

    violations_create = exc_create.value.rejected.violations
    assert violations_create[0].code == ViolationCode.FORBIDDEN_OPERATION
    assert violations_create[0].message == "No tiene permiso para crear bloqueos."


def test_reception_and_admin_pass_always() -> None:
    actor_recep = Actor(user_id=U_RECEP, role=Role.RECEPCION, professional_id=None)
    perm_recep = Permission(actor_recep, Scope.ALL, Resource.WORKING_HOURS, Action.READ)
    ensure_own_professional(perm_recep, P1)
    ensure_own_professional(perm_recep, P2)

    actor_admin = Actor(user_id=U_ADMIN, role=Role.ADMINISTRADOR, professional_id=None)
    perm_admin = Permission(actor_admin, Scope.ALL, Resource.BLOCK, Action.CREATE)
    ensure_own_professional(perm_admin, P1)
    ensure_own_professional(perm_admin, P2)
