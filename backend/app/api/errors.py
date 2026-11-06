from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import AuthErrorCode, AuthErrorResponse, serialize_violation
from app.domain.violations import Rejected, Violation, ViolationCode

VIOLATION_STATUS_MAP: Mapping[ViolationCode, int] = {
    # 409 Conflicto de agenda o unicidad
    ViolationCode.PROFESSIONAL_OVERLAP: 409,
    ViolationCode.CHAIR_OVERLAP: 409,
    ViolationCode.OUTSIDE_WORKING_HOURS: 409,
    ViolationCode.BLOCKED_TIME: 409,
    ViolationCode.DUPLICATE_DNI: 409,
    ViolationCode.DUPLICATE_NAME: 409,
    # 422 Validez del pedido
    ViolationCode.UNKNOWN_REFERENCE: 422,
    ViolationCode.INACTIVE_REFERENCE: 422,
    ViolationCode.INVALID_DURATION: 422,
    ViolationCode.INVALID_START_TIME: 422,
    ViolationCode.CROSSES_MIDNIGHT: 422,
    ViolationCode.IN_THE_PAST: 422,
    ViolationCode.INVALID_WORKING_HOURS: 422,
    ViolationCode.OVERLAPPING_WORKING_HOURS: 422,
    ViolationCode.INVALID_BLOCK: 422,
    ViolationCode.INVALID_DNI: 422,
    ViolationCode.EMPTY_NAME: 422,
    ViolationCode.STATUS_CHANGE_TOO_EARLY: 422,
    ViolationCode.INVALID_TRANSITION: 422,
    # 403 Operación prohibida
    ViolationCode.FORBIDDEN_OPERATION: 403,
}


def unclassified_codes(mapping: Mapping[ViolationCode, int]) -> set[ViolationCode]:
    return set(ViolationCode) - set(mapping.keys())


def status_for(violations: Sequence[Violation | ViolationCode]) -> int:
    statuses = {
        VIOLATION_STATUS_MAP[v.code if isinstance(v, Violation) else v]
        for v in violations
    }
    if 403 in statuses:
        return 403
    if 422 in statuses:
        return 422
    return 409


class DomainRejectedError(Exception):
    def __init__(self, rejected: Rejected) -> None:
        self.rejected = rejected
        super().__init__(f"Domain rejected with {len(rejected.violations)} violation(s)")


def domain_rejected_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainRejectedError):
        raise exc
    status_code = status_for(exc.rejected.violations)
    content = {
        "violations": [serialize_violation(v) for v in exc.rejected.violations]
    }
    return JSONResponse(status_code=status_code, content=content)


AUTH_ERROR_MESSAGES: Mapping[AuthErrorCode, str] = {
    AuthErrorCode.INVALID_CREDENTIALS: "Usuario o contraseña incorrectos.",
    AuthErrorCode.INVALID_TOKEN: "La sesión venció o no es válida. Inicie sesión de nuevo.",
}


class AuthenticationError(Exception):
    def __init__(self, code: AuthErrorCode) -> None:
        self.code = code
        super().__init__(code.value)


def authentication_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AuthenticationError):
        raise exc
    body = AuthErrorResponse(code=exc.code, message=AUTH_ERROR_MESSAGES[exc.code])
    return JSONResponse(
        status_code=401,
        content=body.model_dump(mode="json"),
        headers={"WWW-Authenticate": "Bearer"},
    )


MALFORMED_MESSAGES: Mapping[str, str] = {
    "json_invalid": "El cuerpo no es JSON válido.",
    "missing": "Falta este dato.",
}
DEFAULT_MALFORMED_MESSAGE = "Dato inválido."


def request_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    error_items: list[dict[str, Any]] = []
    for err in exc.errors():
        err_type = str(err.get("type", "invalid"))
        loc = err.get("loc", ())
        field: str | None = None
        if err_type != "json_invalid" and len(loc) > 1:
            field = ".".join(str(elem) for elem in loc[1:])
        message = MALFORMED_MESSAGES.get(err_type, DEFAULT_MALFORMED_MESSAGE)
        error_items.append(
            {
                "field": field,
                "type": err_type,
                "message": message,
            }
        )
    return JSONResponse(status_code=400, content={"errors": error_items})
