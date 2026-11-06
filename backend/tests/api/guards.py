"""Guardianes de rechazo por defecto, como funciones puras sobre una app.

Se prueban también con apps mal armadas: un guardián roto pasaría siempre.
"""

from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, iter_route_contexts

from app.api.deps import RequirePermission, get_current_user


PUBLIC_OPERATIONS = frozenset({("GET", "/api/health"), ("POST", "/api/auth/login")})
PROTECTED_WITHOUT_PERMISSION = frozenset({("GET", "/api/auth/me")})
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


def schema_operations(app: FastAPI) -> set[tuple[str, str]]:
    return {
        (method.upper(), path)
        for path, item in app.openapi()["paths"].items()
        for method in item
        if method in HTTP_METHODS
    }


def routes_without_auth(app: FastAPI) -> set[tuple[str, str]]:
    paths = app.openapi()["paths"]
    return {
        (method, path)
        for method, path in schema_operations(app) - PUBLIC_OPERATIONS
        if not paths[path][method.lower()].get("security")
    }


def _dependency_calls(dependant: Dependant) -> Iterator[object]:
    for dependency in dependant.dependencies:
        yield dependency.call
        yield from _dependency_calls(dependency)


def _api_routes(app: FastAPI) -> Iterator[tuple[set[tuple[str, str]], list[object]]]:
    # FastAPI no aplana los routers incluidos: app.routes solo ve _IncludedRouter.
    for context in iter_route_contexts(app.routes):
        if not isinstance(context.original_route, APIRoute):
            continue
        dependant: Dependant = context.dependant
        operations = {(method, str(context.path)) for method in context.methods or set()}
        yield operations, list(_dependency_calls(dependant))


def protected_routes(app: FastAPI) -> set[tuple[str, str]]:
    protected: set[tuple[str, str]] = set()
    for operations, calls in _api_routes(app):
        if get_current_user in calls:
            protected |= operations
    return protected


def routes_without_permission(app: FastAPI) -> set[tuple[str, str]]:
    missing: set[tuple[str, str]] = set()
    for operations, calls in _api_routes(app):
        if get_current_user not in calls:
            continue
        if any(isinstance(call, RequirePermission) for call in calls):
            continue
        missing |= operations - PROTECTED_WITHOUT_PERMISSION
    return missing
