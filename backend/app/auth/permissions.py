"""Matriz RBAC como tabla de datos, sin FastAPI (RN-AC, design.md de C-19)."""

from collections.abc import Collection, Mapping
from enum import Enum

from app.domain.model import Role


class Resource(Enum):
    APPOINTMENT = "appointment"
    APPOINTMENT_HISTORY = "appointment_history"
    WORKING_HOURS = "working_hours"
    BLOCK = "block"
    PROFESSIONAL = "professional"
    CHAIR = "chair"
    SERVICE = "service"
    PATIENT = "patient"
    USER = "user"


class Action(Enum):
    CREATE = "create"
    READ = "read"
    READ_AGENDA = "read_agenda"
    UPDATE = "update"
    DELETE = "delete"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    CHANGE_STATUS = "change_status"


class Scope(Enum):
    ALL = "all"
    OWN = "own"


Combination = tuple[Resource, Action]

_D = Role.ODONTOLOGO
_R = Role.RECEPCION
_A = Role.ADMINISTRADOR
_ALL = Scope.ALL
_OWN = Scope.OWN

# Un rol sin entrada recibe 403. `Scope.OWN` en CHANGE_STATUS significa "dejar pasar y
# que decida el dominio": la API nunca compara el propietario de un turno.
PERMISSIONS: Mapping[Combination, Mapping[Role, Scope]] = {
    (Resource.APPOINTMENT, Action.CREATE): {_R: _ALL, _A: _ALL},
    (Resource.APPOINTMENT, Action.READ_AGENDA): {_D: _ALL, _R: _ALL, _A: _ALL},
    (Resource.APPOINTMENT, Action.RESCHEDULE): {_R: _ALL, _A: _ALL},
    (Resource.APPOINTMENT, Action.CANCEL): {_R: _ALL, _A: _ALL},
    (Resource.APPOINTMENT, Action.CHANGE_STATUS): {_D: _OWN, _R: _ALL, _A: _ALL},
    (Resource.APPOINTMENT_HISTORY, Action.READ): {_D: _OWN, _R: _ALL, _A: _ALL},
    (Resource.WORKING_HOURS, Action.CREATE): {_D: _OWN, _A: _ALL},
    (Resource.WORKING_HOURS, Action.READ): {_D: _OWN, _R: _ALL, _A: _ALL},
    (Resource.WORKING_HOURS, Action.UPDATE): {_D: _OWN, _A: _ALL},
    (Resource.WORKING_HOURS, Action.DELETE): {_A: _ALL},
    (Resource.BLOCK, Action.CREATE): {_D: _OWN, _A: _ALL},
    (Resource.BLOCK, Action.READ): {_D: _OWN, _R: _ALL, _A: _ALL},
    (Resource.BLOCK, Action.UPDATE): {_D: _OWN, _A: _ALL},
    (Resource.BLOCK, Action.DELETE): {_D: _OWN, _A: _ALL},
    (Resource.PROFESSIONAL, Action.CREATE): {_A: _ALL},
    (Resource.PROFESSIONAL, Action.READ): {_D: _ALL, _R: _ALL, _A: _ALL},
    (Resource.PROFESSIONAL, Action.UPDATE): {_A: _ALL},
    (Resource.PROFESSIONAL, Action.DELETE): {_A: _ALL},
    (Resource.CHAIR, Action.CREATE): {_A: _ALL},
    (Resource.CHAIR, Action.READ): {_D: _ALL, _R: _ALL, _A: _ALL},
    (Resource.CHAIR, Action.UPDATE): {_A: _ALL},
    (Resource.CHAIR, Action.DELETE): {_A: _ALL},
    (Resource.SERVICE, Action.CREATE): {_A: _ALL},
    (Resource.SERVICE, Action.READ): {_D: _ALL, _R: _ALL, _A: _ALL},
    (Resource.SERVICE, Action.UPDATE): {_A: _ALL},
    (Resource.SERVICE, Action.DELETE): {_A: _ALL},
    (Resource.PATIENT, Action.CREATE): {_R: _ALL, _A: _ALL},
    (Resource.PATIENT, Action.READ): {_D: _ALL, _R: _ALL, _A: _ALL},
    (Resource.PATIENT, Action.UPDATE): {_R: _ALL, _A: _ALL},
    (Resource.PATIENT, Action.DELETE): {},
    (Resource.USER, Action.CREATE): {_A: _ALL},
    (Resource.USER, Action.READ): {_A: _ALL},
    (Resource.USER, Action.UPDATE): {_A: _ALL},
    (Resource.USER, Action.DELETE): {_A: _ALL},
}

PERMISSION_MESSAGES: Mapping[Combination, str] = {
    (Resource.APPOINTMENT, Action.CREATE): "No tiene permiso para dar turnos.",
    (Resource.APPOINTMENT, Action.READ_AGENDA): "No tiene permiso para leer la agenda.",
    (Resource.APPOINTMENT, Action.RESCHEDULE): "No tiene permiso para reprogramar turnos.",
    (Resource.APPOINTMENT, Action.CANCEL): "No tiene permiso para cancelar turnos.",
    (Resource.APPOINTMENT, Action.CHANGE_STATUS): "No tiene permiso para cambiar el estado de turnos.",
    (Resource.APPOINTMENT_HISTORY, Action.READ): "No tiene permiso para leer el historial de turnos.",
    (Resource.WORKING_HOURS, Action.CREATE): "No tiene permiso para crear horarios.",
    (Resource.WORKING_HOURS, Action.READ): "No tiene permiso para leer horarios.",
    (Resource.WORKING_HOURS, Action.UPDATE): "No tiene permiso para actualizar horarios.",
    (Resource.WORKING_HOURS, Action.DELETE): "No tiene permiso para borrar horarios.",
    (Resource.BLOCK, Action.CREATE): "No tiene permiso para crear bloqueos.",
    (Resource.BLOCK, Action.READ): "No tiene permiso para leer bloqueos.",
    (Resource.BLOCK, Action.UPDATE): "No tiene permiso para actualizar bloqueos.",
    (Resource.BLOCK, Action.DELETE): "No tiene permiso para borrar bloqueos.",
    (Resource.PROFESSIONAL, Action.CREATE): "No tiene permiso para crear profesionales.",
    (Resource.PROFESSIONAL, Action.READ): "No tiene permiso para leer profesionales.",
    (Resource.PROFESSIONAL, Action.UPDATE): "No tiene permiso para actualizar profesionales.",
    (Resource.PROFESSIONAL, Action.DELETE): "No tiene permiso para borrar profesionales.",
    (Resource.CHAIR, Action.CREATE): "No tiene permiso para crear sillones.",
    (Resource.CHAIR, Action.READ): "No tiene permiso para leer sillones.",
    (Resource.CHAIR, Action.UPDATE): "No tiene permiso para actualizar sillones.",
    (Resource.CHAIR, Action.DELETE): "No tiene permiso para borrar sillones.",
    (Resource.SERVICE, Action.CREATE): "No tiene permiso para crear prestaciones.",
    (Resource.SERVICE, Action.READ): "No tiene permiso para leer prestaciones.",
    (Resource.SERVICE, Action.UPDATE): "No tiene permiso para actualizar prestaciones.",
    (Resource.SERVICE, Action.DELETE): "No tiene permiso para borrar prestaciones.",
    (Resource.PATIENT, Action.CREATE): "No tiene permiso para crear pacientes.",
    (Resource.PATIENT, Action.READ): "No tiene permiso para leer pacientes.",
    (Resource.PATIENT, Action.UPDATE): "No tiene permiso para actualizar pacientes.",
    (Resource.PATIENT, Action.DELETE): "No tiene permiso para borrar pacientes.",
    (Resource.USER, Action.CREATE): "No tiene permiso para crear usuarios.",
    (Resource.USER, Action.READ): "No tiene permiso para leer usuarios.",
    (Resource.USER, Action.UPDATE): "No tiene permiso para actualizar usuarios.",
    (Resource.USER, Action.DELETE): "No tiene permiso para borrar usuarios.",
}


def scope_for(resource: Resource, action: Action, role: Role) -> Scope | None:
    return PERMISSIONS.get((resource, action), {}).get(role)


def missing_combinations(
    permissions: Mapping[Combination, Mapping[Role, Scope]],
    expected: Collection[Combination],
) -> frozenset[Combination]:
    return frozenset(expected) - frozenset(permissions)
