"""Resultado de catálogo separado del resultado de agenda con appointment."""

from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

from app.domain.model import Chair, Patient, Professional, Service
from app.domain.violations import Rejected

T = TypeVar("T", Professional, Chair, Service, Patient)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Entidad aceptada por un alta, sin persistir ni modificar la candidata."""

    entity: T


CatalogResult: TypeAlias = Ok[T] | Rejected
