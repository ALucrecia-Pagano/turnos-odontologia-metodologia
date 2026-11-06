from dataclasses import dataclass, field
from uuid import UUID

from app.domain.model import Actor, Role


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Usuario confirmado contra la base. Nunca lleva el hash."""

    id: UUID
    username: str
    display_name: str
    role: Role
    professional_id: UUID | None

    def to_actor(self) -> Actor:
        return Actor(
            user_id=self.id,
            role=self.role,
            professional_id=self.professional_id,
        )


@dataclass(frozen=True, slots=True)
class StoredUser:
    """Lectura de un usuario por id: incluye `active`, que no pasa a las rutas."""

    user: AuthenticatedUser
    active: bool


@dataclass(frozen=True, slots=True)
class UserCredentials:
    """Unico tipo que lleva el hash, y solo lo usa el login."""

    user: AuthenticatedUser
    active: bool
    password_hash: str = field(repr=False)
