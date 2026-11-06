from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.schemas import (
    AuthErrorResponse,
    MalformedRequestResponse,
    NotFoundErrorResponse,
    ViolationResponseSchema,
)


def violation_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    responses: dict[int | str, dict[str, Any]] = {}
    for code in status_codes:
        if code == 409:
            example = {
                "violations": [
                    {
                        "code": "PROFESSIONAL_OVERLAP",
                        "message": "La Dra. Laura Quiroga ya tiene un turno de 10:00 a 10:30 (turno a1b2).",
                        "conflictingAppointmentId": "00000000-0000-0000-0000-00000000a1b2",
                        "conflictingInterval": {
                            "startAt": "2026-10-20T13:00:00Z",
                            "endAt": "2026-10-20T13:30:00Z",
                        },
                    }
                ]
            }
            desc = "Conflicto de agenda o unicidad"
        elif code == 422:
            example = {
                "violations": [
                    {
                        "code": "INVALID_DURATION",
                        "message": "La duración debe ser múltiplo de 5 minutos.",
                    }
                ]
            }
            desc = "Regla de validez del dominio"
        elif code == 403:
            example = {
                "violations": [
                    {
                        "code": "FORBIDDEN_OPERATION",
                        "message": "No tiene permisos para modificar este turno.",
                    }
                ]
            }
            desc = "Operación prohibida"
        else:
            example = {
                "violations": [
                    {
                        "code": "UNKNOWN_REFERENCE",
                        "message": "Referencia no encontrada.",
                    }
                ]
            }
            desc = "Rechazo del dominio"

        responses[code] = {
            "model": ViolationResponseSchema,
            "description": desc,
            "content": {
                "application/json": {
                    "example": example,
                }
            },
        }
    return responses


def permission_responses() -> dict[int | str, dict[str, Any]]:
    responses = violation_responses(403)
    responses[403]["description"] = "El rol no tiene permiso para esta operación"
    responses[403]["content"]["application/json"]["example"] = {
        "violations": [
            {
                "code": "FORBIDDEN_OPERATION",
                "message": "No tiene permiso para dar turnos.",
            }
        ]
    }
    return responses


def login_responses() -> dict[int | str, dict[str, Any]]:
    return {
        401: {
            "model": AuthErrorResponse,
            "description": "Credenciales inválidas",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Usuario o contraseña incorrectos.",
                    }
                }
            },
        }
    }


def not_found_responses(resource_name: str) -> dict[int | str, dict[str, Any]]:
    return {
        404: {
            "model": NotFoundErrorResponse,
            "description": f"{resource_name} no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "code": "NOT_FOUND",
                        "message": f"{resource_name} no encontrado.",
                    }
                }
            },
        }
    }


def setup_openapi(app: FastAPI) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )

        components: dict[str, Any] = openapi_schema.setdefault("components", {})
        schemas: dict[str, Any] = components.setdefault("schemas", {})

        if "MalformedRequestResponse" not in schemas:
            malformed_schema = MalformedRequestResponse.model_json_schema(
                ref_template="#/components/schemas/{model}"
            )
            if "$defs" in malformed_schema:
                for def_name, def_val in malformed_schema["$defs"].items():
                    schemas[def_name] = def_val
                del malformed_schema["$defs"]
            schemas["MalformedRequestResponse"] = malformed_schema

        if "AuthErrorResponse" not in schemas:
            auth_error_schema = AuthErrorResponse.model_json_schema(
                ref_template="#/components/schemas/{model}"
            )
            for def_name, def_val in auth_error_schema.pop("$defs", {}).items():
                schemas[def_name] = def_val
            schemas["AuthErrorResponse"] = auth_error_schema

        paths: dict[str, Any] = openapi_schema.get("paths", {})
        for path_item in paths.values():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue
                has_input = bool(
                    operation.get("parameters") or operation.get("requestBody")
                )
                responses: dict[str, Any] = operation.setdefault("responses", {})
                if has_input and "400" not in responses:
                    responses["400"] = {
                        "description": "Entrada malformada",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/MalformedRequestResponse"
                                }
                            }
                        },
                    }

                if operation.get("security") and "401" not in responses:
                    responses["401"] = {
                        "description": "Token ausente, vencido o inválido",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/AuthErrorResponse"
                                },
                                "example": {
                                    "code": "INVALID_TOKEN",
                                    "message": "La sesión venció o no es válida. Inicie sesión de nuevo.",
                                },
                            }
                        },
                    }

                resp_422 = responses.get("422")
                if isinstance(resp_422, dict):
                    schema_ref = (
                        resp_422.get("content", {})
                        .get("application/json", {})
                        .get("schema", {})
                        .get("$ref", "")
                    )
                    if "HTTPValidationError" in schema_ref:
                        del responses["422"]

        schemas.pop("HTTPValidationError", None)
        schemas.pop("ValidationError", None)

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    setattr(app, "openapi", custom_openapi)
