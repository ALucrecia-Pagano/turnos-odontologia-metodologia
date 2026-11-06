from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.api.errors import AuthenticationError, DomainRejectedError
from app.api.schemas import AuthErrorCode
from app.auth.model import AuthenticatedUser
from app.auth.permissions import PERMISSION_MESSAGES, Action, Resource, Scope, scope_for
from app.auth.tokens import decode_access_token
from app.config import Settings
from app.domain.model import Actor
from app.domain.violations import Rejected, Violation, ViolationCode
from app.repositories.users import UserRepository


def get_db_session(request: Request) -> Iterator[Session]:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    with session_factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="bearerAuth",
    bearerFormat="JWT",
    description="Pegue el accessToken de POST /api/auth/login, sin la palabra Bearer.",
)


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db_session)],
) -> AuthenticatedUser:
    if credentials is None:
        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)
    settings: Settings = request.app.state.settings
    claims = decode_access_token(credentials.credentials, settings)
    if claims is None:
        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)
    stored = UserRepository(session).get_by_id(claims.user_id)
    if stored is None:
        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)
    if not stored.active:
        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)
    if stored.user.role is not claims.role:
        raise AuthenticationError(AuthErrorCode.INVALID_TOKEN)
    return stored.user


# Los routers de negocio cuelgan de este: ninguna ruta nace sin autenticación.
protected_router = APIRouter(dependencies=[Depends(get_current_user)])


def get_current_actor(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> Actor:
    return user.to_actor()


@dataclass(frozen=True, slots=True)
class Permission:
    """Lo que recibe una ruta con permiso: el `Actor` y su alcance en esa celda."""

    actor: Actor
    scope: Scope


class RequirePermission:
    """Dependencia de una celda de la matriz. Es una clase para que los guardianes la vean."""

    def __init__(self, resource: Resource, action: Action) -> None:
        self.resource = resource
        self.action = action

    def __call__(
        self, user: Annotated[AuthenticatedUser, Depends(get_current_user)]
    ) -> Permission:
        scope = scope_for(self.resource, self.action, user.role)
        if scope is None:
            raise DomainRejectedError(
                Rejected(
                    (
                        Violation(
                            ViolationCode.FORBIDDEN_OPERATION,
                            PERMISSION_MESSAGES[(self.resource, self.action)],
                        ),
                    )
                )
            )
        return Permission(user.to_actor(), scope)


def require_permission(resource: Resource, action: Action) -> RequirePermission:
    return RequirePermission(resource, action)
