from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import jwt

from app.auth.model import AuthenticatedUser
from app.config import Settings
from app.domain.model import Role


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: UUID
    role: Role


def create_access_token(
    user: AuthenticatedUser, settings: Settings, now: datetime
) -> str:
    expires_at = now + timedelta(minutes=settings.jwt_expires_min)
    return jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": int(expires_at.timestamp()),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> TokenClaims | None:
    """Devuelve los claims, o `None` ante cualquier token inválido o vencido."""
    try:
        payload: Mapping[str, object] = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "role"]},
        )
        return TokenClaims(
            user_id=UUID(str(payload["sub"])),
            role=Role(payload["role"]),
        )
    except (jwt.InvalidTokenError, ValueError):
        return None
