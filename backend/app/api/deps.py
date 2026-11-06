from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

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
    resource: Resource | None = None
    action: Action | None = None


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
        return Permission(user.to_actor(), scope, self.resource, self.action)


def require_permission(resource: Resource, action: Action) -> RequirePermission:
    return RequirePermission(resource, action)


def ensure_own_professional(
    permission: Permission,
    professional_id: UUID,
    resource: Resource | None = None,
    action: Action | None = None,
) -> None:
    """Valida que un actor con Scope.OWN solo opere sobre su propio profesional (D3).

    Si permission.scope es Scope.OWN y professional_id no coincide con el del Actor,
    lanza 403 FORBIDDEN_OPERATION con el mensaje de PERMISSION_MESSAGES de esa celda.
    Si permission.scope es Scope.ALL (recepción, administrador), pasa siempre.
    """
    if permission.scope is Scope.OWN:
        if permission.actor.professional_id != professional_id:
            res = resource or permission.resource
            act = action or permission.action
            message = (
                PERMISSION_MESSAGES.get((res, act))
                if res and act
                else None
            )
            if message is None:
                message = "No tiene permiso para realizar esta operación sobre otro profesional."
            raise DomainRejectedError(
                Rejected(
                    (
                        Violation(
                            code=ViolationCode.FORBIDDEN_OPERATION,
                            message=message,
                        ),
                    )
                )
            )
