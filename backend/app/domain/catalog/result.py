"""Resultado de catálogo separado del resultado de agenda con appointment."""

from dataclasses import dataclass
from typing import Generic, TypeAlias, TypeVar

from app.domain.model import Block, Chair, Patient, Professional, Service, WorkingHours
from app.domain.violations import Rejected

T = TypeVar(
    "T",
    Professional,
    Chair,
    Service,
    Patient,
    Block,
    tuple[WorkingHours, ...],
)


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Entidad aceptada por un alta, sin persistir ni modificar la candidata."""

    entity: T


CatalogResult: TypeAlias = Ok[T] | Rejected
