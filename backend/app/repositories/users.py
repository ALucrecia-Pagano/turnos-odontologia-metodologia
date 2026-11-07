from collections.abc import Collection
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, defer

from app.auth.model import AuthenticatedUser, StoredUser, UserCredentials
from app.db.models import UserModel
from app.domain.model import Role
from app.repositories._integrity import constraint_name


class UserWriteError(Exception):
    """Fallo de escritura de un usuario: nombra la restricción, nunca la fila."""

    def __init__(self, constraint: str | None) -> None:
        self.constraint = constraint
        super().__init__(f"No se pudo guardar el usuario: {constraint}")


def _to_user(row: UserModel) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=row.id,
        username=row.username,
        display_name=row.display_name,
        role=Role(row.role),
        professional_id=row.professional_id,
    )


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_credentials_by_username(self, username: str) -> UserCredentials | None:
        row = self._session.scalars(
            select(UserModel).where(UserModel.username == username)
        ).first()
        if row is None:
            return None
        return UserCredentials(
            user=_to_user(row),
            active=row.active,
            password_hash=row.password_hash,
        )

    def get_by_id(self, identifier: UUID) -> StoredUser | None:
        row = self._session.get(
            UserModel, identifier, options=[defer(UserModel.password_hash, raiseload=True)]
        )
        if row is None:
            return None
        return StoredUser(user=_to_user(row), active=row.active)

    def get_display_names(self, ids: Collection[UUID]) -> dict[UUID, str]:
        unique_ids = set(ids)
        if not unique_ids:
            return {}
        stmt = select(UserModel.id, UserModel.display_name).where(UserModel.id.in_(unique_ids))
        rows = self._session.execute(stmt).all()
        return {row.id: row.display_name for row in rows}


    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(UserModel)) or 0

    def create(self, user: AuthenticatedUser, password_hash: str) -> None:
        row = UserModel(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            password_hash=password_hash,
            role=user.role.value,
            professional_id=user.professional_id,
        )
        try:
            with self._session.begin_nested():
                self._session.add(row)
                self._session.flush()
        except IntegrityError as error:
            # El DETAIL de PostgreSQL incluye la fila, con el hash: no se encadena.
            raise UserWriteError(constraint_name(error)) from None
