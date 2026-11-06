from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session, protected_router
from app.api.errors import AuthenticationError
from app.api.openapi import login_responses
from app.api.schemas import AuthErrorCode
from app.auth.login import authenticate
from app.auth.model import AuthenticatedUser
from app.auth.tokens import create_access_token
from app.config import Settings
from app.domain.model import Role
from app.repositories.users import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=150)
    password: SecretStr = Field(min_length=1, max_length=128)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"username": "recepcion", "password": "pegue-aca-su-contraseña"}
        },
    )


class TokenResponse(BaseModel):
    access_token: str = Field(serialization_alias="accessToken")
    token_type: Literal["bearer"] = Field(default="bearer", serialization_alias="tokenType")

    model_config = ConfigDict(populate_by_name=True)


class CurrentUserResponse(BaseModel):
    id: UUID
    username: str
    display_name: str = Field(serialization_alias="displayName")
    role: Role
    professional_id: UUID | None = Field(serialization_alias="professionalId")

    model_config = ConfigDict(populate_by_name=True)


@router.post("/login", response_model=TokenResponse, responses=login_responses())
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> TokenResponse:
    user = authenticate(
        UserRepository(session), body.username, body.password.get_secret_value()
    )
    if user is None:
        raise AuthenticationError(AuthErrorCode.INVALID_CREDENTIALS)
    settings: Settings = request.app.state.settings
    response.headers["Cache-Control"] = "no-store"
    return TokenResponse(
        access_token=create_access_token(user, settings, datetime.now(UTC))
    )


@protected_router.get("/auth/me", tags=["auth"], response_model=CurrentUserResponse)
def me(user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        professional_id=user.professional_id,
    )
