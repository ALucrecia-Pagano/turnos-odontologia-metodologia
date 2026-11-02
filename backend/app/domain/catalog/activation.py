"""Cambios de actividad por copia; no reciben ni modifican turnos."""

from dataclasses import replace
from typing import TypeVar

from app.domain.model import Chair, Professional, Service

Resource = TypeVar("Resource", Professional, Chair, Service)


def deactivate(candidate: Resource) -> Resource:
    """Copia del mismo tipo con active=False; idempotente por valores."""
    return replace(candidate, active=False)


def reactivate(candidate: Resource) -> Resource:
    """Copia del mismo tipo con active=True; idempotente por valores."""
    return replace(candidate, active=True)
