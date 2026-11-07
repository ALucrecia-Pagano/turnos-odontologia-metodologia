"""Verificacion por mutacion, reproducible, de los tests de C-23.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-23.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de produccion.
Por cada una: comprueba que el original aparezca exactamente una vez, aplica la
mutacion, corre solo su test, restaura el archivo en un finally y vuelve a correr el test.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-23.txt y regenera la tabla de
verify-C-23.md leyendo ese .txt. Termina con codigo 0 solo si todas las mutaciones
hicieron fallar su test, ninguna es INVALIDA y el SHA-256 no cambio.

Una mutacion es INVALIDA si su test no la detecta con una afirmacion propia: la salida
contiene NameError o ImportError, o el primer "E" no tiene su frame en tests/, o no es
assert/AssertionError. Dentro de tests/ tambien valen pytest.raises sin excepcion
("Failed: DID NOT RAISE"), un ValidationError del esquema que el test valida directamente
y un KeyError/IndexError sobre un campo que el propio test lee.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "mutaciones-C-23.txt"
VERIFY = EVIDENCE / "verify-C-23.md"
TABLE_START = "<!-- mutaciones:inicio -->"
TABLE_END = "<!-- mutaciones:fin -->"
SEPARATOR = "=" * 80
TIMEOUT_SECONDS = 180

INVALID_NAME_ERROR = re.compile(r"\b(NameError|ImportError|ModuleNotFoundError)\b")
FRAME_LINE = re.compile(r"^(\S+\.py):\d+: ")
TEST_DETECTION = re.compile(
    r"""^(assert\b|AssertionError\b|Failed: DID NOT RAISE\b"""
    r"""|pydantic_core\._pydantic_core\.ValidationError\b"""
    r"""|KeyError: ['"]|IndexError\b)"""
)

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

TEST_SCHEMAS = "tests/api/test_appointment_lifecycle_schemas.py"
TEST_USER_REPO = "tests/integration/test_user_repository.py"
TEST_SERVICES = "tests/integration/test_appointment_lifecycle_services.py"
TEST_CANCEL = "tests/integration/test_api_appointment_cancel.py"
TEST_RESCHEDULE = "tests/integration/test_api_appointment_reschedule.py"
TEST_STATUS = "tests/integration/test_api_appointment_status.py"
TEST_HISTORY = "tests/integration/test_api_appointment_history.py"
TEST_OPENAPI = "tests/integration/test_appointment_lifecycle_openapi.py"

API_SCHEMAS = "backend/app/api/schemas.py"
REPOSITORY_USERS = "backend/app/repositories/users.py"
SERVICE_APPOINTMENTS = "backend/app/services/appointments.py"
API_APPOINTMENTS = "backend/app/api/appointments.py"
API_ERRORS = "backend/app/api/errors.py"

# Un turno inexistente responde 200 con datos inventados en lugar de 404.
FABRICATED_APPOINTMENT = (
    '        return AppointmentResponse(\n'
    '            id=id, patient_id=id, professional_id=id, chair_id=id, service_id=id,\n'
    '            start_at=format_utc_iso(now), end_at=format_utc_iso(now), status="reservado",\n'
    '        )'
)


@dataclass(frozen=True)
class Mutation:
    test_file: str
    test_name: str
    file: str
    original: str
    mutated: str

    @property
    def node_id(self) -> str:
        return f"{self.test_file}::{self.test_name}"

    @property
    def function_name(self) -> str:
        return self.test_name.split("[", 1)[0]


MUTATIONS: tuple[Mutation, ...] = (
    # 1. Esquemas - valid statuses
    Mutation(
        TEST_SCHEMAS,
        "test_status_change_input_valid_statuses",
        API_SCHEMAS,
        'AllowedStatusChange = Literal["confirmado", "atendido", "ausente"]',
        'AllowedStatusChange = Literal["confirmado_mutado", "atendido", "ausente"]',
    ),
    # 2. Esquemas - cancelado rechazado
    Mutation(
        TEST_SCHEMAS,
        "test_status_change_input_cancelado_rejected",
        API_SCHEMAS,
        'class StatusChangeInput(BaseModel):\n'
        '    to_status: AllowedStatusChange = Field(alias="toStatus")',
        'class StatusChangeInput(BaseModel):\n'
        '    to_status: str = Field(alias="toStatus")',
    ),
    # 3. Esquemas - reservado rechazado
    Mutation(
        TEST_SCHEMAS,
        "test_status_change_input_reservado_rejected",
        API_SCHEMAS,
        'AllowedStatusChange = Literal["confirmado", "atendido", "ausente"]',
        'AllowedStatusChange = Literal["confirmado", "atendido", "ausente", "reservado"]',
    ),
    # 4. Esquemas - extra field rechazado en StatusChangeInput
    Mutation(
        TEST_SCHEMAS,
        "test_status_change_input_extra_field_forbidden",
        API_SCHEMAS,
        'class StatusChangeInput(BaseModel):\n'
        '    to_status: AllowedStatusChange = Field(alias="toStatus")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        'class StatusChangeInput(BaseModel):\n'
        '    to_status: AllowedStatusChange = Field(alias="toStatus")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="allow")',
    ),
    # 5. Esquemas - RescheduleInput start_at with tz accepted
    Mutation(
        TEST_SCHEMAS,
        "test_reschedule_input_start_at_with_tz_accepted",
        API_SCHEMAS,
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is None:\n'
        '            raise ValueError("La fecha y hora debe incluir zona horaria.")\n'
        '        return v\n\n\n'
        'class RescheduleDetailResponse',
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is not None:\n'
        '            raise ValueError("La fecha y hora debe incluir zona horaria.")\n'
        '        return v\n\n\n'
        'class RescheduleDetailResponse',
    ),
    # 6. Esquemas - RescheduleInput minimal accepted
    Mutation(
        TEST_SCHEMAS,
        "test_reschedule_input_minimal_accepted",
        API_SCHEMAS,
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")',
        '    professional_id: UUID = Field(alias="professionalId")',
    ),
    # 7. Esquemas - RescheduleInput start_at without tz rejected
    Mutation(
        TEST_SCHEMAS,
        "test_reschedule_input_start_at_without_tz_rejected",
        API_SCHEMAS,
        'class RescheduleInput(BaseModel):\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")\n'
        '    chair_id: UUID | None = Field(default=None, alias="chairId")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")\n\n'
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is None:',
        'class RescheduleInput(BaseModel):\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")\n'
        '    chair_id: UUID | None = Field(default=None, alias="chairId")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")\n\n'
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if False and v.tzinfo is None:',
    ),
    # 8. Esquemas - RescheduleInput extra field forbidden
    Mutation(
        TEST_SCHEMAS,
        "test_reschedule_input_extra_field_forbidden",
        API_SCHEMAS,
        'class RescheduleInput(BaseModel):\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")\n'
        '    chair_id: UUID | None = Field(default=None, alias="chairId")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        'class RescheduleInput(BaseModel):\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")\n'
        '    chair_id: UUID | None = Field(default=None, alias="chairId")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="allow")',
    ),
    # 9. Esquemas - HistoryEntry initial entry serializes from and reschedule as null
    Mutation(
        TEST_SCHEMAS,
        "test_history_entry_initial_entry_serializes_from_and_reschedule_as_null",
        API_SCHEMAS,
        '    from_status: str | None = Field(default=None, serialization_alias="from")',
        '    from_status: str | None = Field(default=None, serialization_alias="fromStatus")',
    ),
    # 10. Esquemas - HistoryEntry reschedule detail flat eight fields
    Mutation(
        TEST_SCHEMAS,
        "test_history_entry_reschedule_detail_flat_eight_fields",
        API_SCHEMAS,
        'class RescheduleDetailResponse(BaseModel):\n'
        '    previous_start_at: str = Field(serialization_alias="previousStartAt")',
        'class RescheduleDetailResponse(BaseModel):\n'
        '    previous_start_at: str = Field(serialization_alias="prevStartAt")',
    ),
    # 11. Repositorio Users - get_display_names empty list makes zero queries
    Mutation(
        TEST_USER_REPO,
        "test_get_display_names_empty_list_makes_zero_queries",
        REPOSITORY_USERS,
        '    def get_display_names(self, ids: Collection[UUID]) -> dict[UUID, str]:\n'
        '        unique_ids = set(ids)\n'
        '        if not unique_ids:\n'
        '            return {}',
        '    def get_display_names(self, ids: Collection[UUID]) -> dict[UUID, str]:\n'
        '        unique_ids = set(ids)\n'
        '        if not unique_ids:\n'
        '            return {UUID("00000000-0000-0000-0000-000000000001"): "Inesperado"}',
    ),
    # 12. Repositorio Users - get_display_names resolves in single query
    Mutation(
        TEST_USER_REPO,
        "test_get_display_names_resolves_in_single_query",
        REPOSITORY_USERS,
        '        stmt = select(UserModel.id, UserModel.display_name).where(UserModel.id.in_(unique_ids))',
        '        stmt = select(UserModel.id, UserModel.display_name).where(UserModel.id.not_in(unique_ids))',
    ),
    # 13. Servicios - get_appointment_history returns none if not found
    Mutation(
        TEST_SERVICES,
        "test_get_appointment_history_returns_none_if_appointment_not_found",
        SERVICE_APPOINTMENTS,
        '    appointment = app_repo.get_by_id(appointment_id)\n'
        '    if appointment is None:\n'
        '        return None',
        '    appointment = app_repo.get_by_id(appointment_id)\n'
        '    if appointment is None:\n'
        '        return []',
    ),
    # 14. Servicios - get_appointment_history ascending order and reschedule mapping
    Mutation(
        TEST_SERVICES,
        "test_get_appointment_history_ascending_order_and_reschedule_mapping",
        SERVICE_APPOINTMENTS,
        '    status_repo = AppointmentStatusChangeRepository(session)\n'
        '    changes = status_repo.list_by_appointment_id(appointment_id)',
        '    status_repo = AppointmentStatusChangeRepository(session)\n'
        '    changes = list(reversed(status_repo.list_by_appointment_id(appointment_id)))',
    ),
    # 15. Servicios - get_appointment_history unknown user leaves changed_by_name null
    Mutation(
        TEST_SERVICES,
        "test_get_appointment_history_unknown_user_leaves_changed_by_name_null",
        SERVICE_APPOINTMENTS,
        '        changed_name = names_by_id.get(c.changed_by)',
        '        changed_name = names_by_id.get(c.changed_by) or "Usuario Ficticio"',
    ),
    # 16. API Cancel - reception cancels reserved
    Mutation(
        TEST_CANCEL,
        "test_reception_cancels_reserved_appointment",
        API_APPOINTMENTS,
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=False,\n'
        '    )',
    ),
    # 17. API Cancel - admin cancels confirmed
    Mutation(
        TEST_CANCEL,
        "test_admin_cancels_confirmed_appointment",
        API_APPOINTMENTS,
        'def cancel_appointment_endpoint(\n'
        '    id: UUID,\n'
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)),\n'
        '    ],\n'
        '    request: Request,\n'
        '    session: Annotated[Session, Depends(get_db_session)],\n'
        ') -> AppointmentResponse:\n'
        '    settings: Settings = request.app.state.settings\n'
        '    now = datetime.now(UTC)\n'
        '    tz = ZoneInfo(settings.app_timezone)\n\n'
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise DomainRejectedError(result)\n\n'
        '    assert isinstance(result, Ok)\n'
        '    appointment = result.appointment\n'
        '    return AppointmentResponse(\n'
        '        id=appointment.id,\n'
        '        patient_id=appointment.patient_id,\n'
        '        professional_id=appointment.professional_id,\n'
        '        chair_id=appointment.chair_id,\n'
        '        service_id=appointment.service_id,\n'
        '        start_at=format_utc_iso(appointment.interval.start),\n'
        '        end_at=format_utc_iso(appointment.interval.end),\n'
        '        status=appointment.status.value,',
        'def cancel_appointment_endpoint(\n'
        '    id: UUID,\n'
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)),\n'
        '    ],\n'
        '    request: Request,\n'
        '    session: Annotated[Session, Depends(get_db_session)],\n'
        ') -> AppointmentResponse:\n'
        '    settings: Settings = request.app.state.settings\n'
        '    now = datetime.now(UTC)\n'
        '    tz = ZoneInfo(settings.app_timezone)\n\n'
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise DomainRejectedError(result)\n\n'
        '    assert isinstance(result, Ok)\n'
        '    appointment = result.appointment\n'
        '    return AppointmentResponse(\n'
        '        id=appointment.id,\n'
        '        patient_id=appointment.patient_id,\n'
        '        professional_id=appointment.professional_id,\n'
        '        chair_id=appointment.chair_id,\n'
        '        service_id=appointment.service_id,\n'
        '        start_at=format_utc_iso(appointment.interval.start),\n'
        '        end_at=format_utc_iso(appointment.interval.end),\n'
        '        status="reservado",',
    ),
    # 18. API Cancel - attended returns 422
    Mutation(
        TEST_CANCEL,
        "test_cancel_attended_appointment_returns_422",
        API_APPOINTMENTS,
        'def cancel_appointment_endpoint(\n'
        '    id: UUID,\n'
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)),\n'
        '    ],\n'
        '    request: Request,\n'
        '    session: Annotated[Session, Depends(get_db_session)],\n'
        ') -> AppointmentResponse:\n'
        '    settings: Settings = request.app.state.settings\n'
        '    now = datetime.now(UTC)\n'
        '    tz = ZoneInfo(settings.app_timezone)\n\n'
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise DomainRejectedError(result)',
        'def cancel_appointment_endpoint(\n'
        '    id: UUID,\n'
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)),\n'
        '    ],\n'
        '    request: Request,\n'
        '    session: Annotated[Session, Depends(get_db_session)],\n'
        ') -> AppointmentResponse:\n'
        '    settings: Settings = request.app.state.settings\n'
        '    now = datetime.now(UTC)\n'
        '    tz = ZoneInfo(settings.app_timezone)\n\n'
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise NotFoundError("Turno no encontrado.")',
    ),
    # 19. API Cancel - already cancelled returns 422
    Mutation(
        TEST_CANCEL,
        "test_cancel_already_cancelled_appointment_returns_422",
        API_APPOINTMENTS,
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n'
        '    if isinstance(result, Rejected):\n'
        '        result = None\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
    ),
    # 20. API Cancel - nonexistent returns 404
    Mutation(
        TEST_CANCEL,
        "test_cancel_nonexistent_appointment_returns_404",
        API_APPOINTMENTS,
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    result = cancel_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        f'{FABRICATED_APPOINTMENT}',
    ),
    # 21. API Cancel - dentist cannot cancel returns 403
    Mutation(
        TEST_CANCEL,
        "test_dentist_cannot_cancel_appointment_returns_403",
        API_APPOINTMENTS,
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)),',
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CHANGE_STATUS)),',
    ),
    # 22. API Reschedule - start only preserves duration
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_start_only_preserves_real_duration_and_returns_to_reservado",
        API_APPOINTMENTS,
        '    tz = ZoneInfo(settings.app_timezone)\n\n'
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,\n'
        '        duration_min=body.duration_min,\n'
        '    )',
        '    tz = ZoneInfo(settings.app_timezone)\n\n'
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,\n'
        '        duration_min=999,\n'
        '    )',
    ),
    # 23. API Reschedule - explicit professional chair and duration
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_with_explicit_professional_chair_and_duration",
        API_APPOINTMENTS,
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,',
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=None,',
    ),
    # 24. API Reschedule - professional overlap returns 409
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_professional_overlap_returns_409",
        API_APPOINTMENTS,
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,',
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=None,',
    ),
    # 25. API Reschedule - chair overlap returns 409
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_chair_overlap_returns_409",
        API_APPOINTMENTS,
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,',
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=None,',
    ),
    # 26. API Reschedule - inside block returns 409
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_inside_block_returns_409",
        API_APPOINTMENTS,
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,\n'
        '        duration_min=body.duration_min,\n'
        '    )\n\n'
        '    result = reschedule_appointment(',
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at.replace(hour=14),\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,\n'
        '        duration_min=body.duration_min,\n'
        '    )\n\n'
        '    result = reschedule_appointment(',
    ),
    # 27. API Reschedule - outside working hours returns 409
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_outside_working_hours_returns_409",
        API_APPOINTMENTS,
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at,\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,\n'
        '        duration_min=body.duration_min,\n'
        '    )',
        '    reschedule_req = RescheduleRequest(\n'
        '        start_at=body.start_at.replace(hour=10),\n'
        '        professional_id=body.professional_id,\n'
        '        chair_id=body.chair_id,\n'
        '        duration_min=body.duration_min,\n'
        '    )',
    ),
    # 28. API Reschedule - in the past returns 422
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_in_the_past_returns_422",
        API_APPOINTMENTS,
        '    result = reschedule_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        request=reschedule_req,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
        '    result = reschedule_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        request=reschedule_req,\n'
        '        actor=permission.actor,\n'
        '        now=datetime(2000, 1, 1, tzinfo=UTC),\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
    ),
    # 29. API Reschedule - startAt without timezone returns 400
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_start_at_without_timezone_returns_400",
        API_SCHEMAS,
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is None:\n'
        '            raise ValueError("La fecha y hora debe incluir zona horaria.")\n'
        '        return v\n\n\n'
        'class RescheduleDetailResponse',
        '    @field_validator("start_at")\n'
        '    @classmethod\n'
        '    def validate_tz(cls, v: datetime) -> datetime:\n'
        '        if v.tzinfo is None:\n'
        '            return v.replace(tzinfo=timezone.utc)\n'
        '        return v\n\n\n'
        'class RescheduleDetailResponse',
    ),
    # 30. API Reschedule - extra field returns 400
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_extra_field_returns_400",
        API_SCHEMAS,
        'class RescheduleInput(BaseModel):\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")\n'
        '    chair_id: UUID | None = Field(default=None, alias="chairId")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        'class RescheduleInput(BaseModel):\n'
        '    start_at: datetime = Field(alias="startAt")\n'
        '    professional_id: UUID | None = Field(default=None, alias="professionalId")\n'
        '    chair_id: UUID | None = Field(default=None, alias="chairId")\n'
        '    duration_min: int | None = Field(default=None, alias="durationMin")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="ignore")',
    ),
    # 31. API Reschedule - nonexistent returns 404
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_nonexistent_appointment_returns_404",
        API_APPOINTMENTS,
        '    result = reschedule_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        request=reschedule_req,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    result = reschedule_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        request=reschedule_req,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        f'{FABRICATED_APPOINTMENT}',
    ),
    # 32. API Reschedule - dentist cannot reschedule returns 403
    Mutation(
        TEST_RESCHEDULE,
        "test_dentist_cannot_reschedule_returns_403",
        API_APPOINTMENTS,
        '        Depends(require_permission(Resource.APPOINTMENT, Action.RESCHEDULE)),',
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CHANGE_STATUS)),',
    ),
    # 33. API Reschedule - terminal state returns 422
    Mutation(
        TEST_RESCHEDULE,
        "test_reschedule_terminal_state_appointment_returns_422",
        API_APPOINTMENTS,
        '    result = reschedule_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        request=reschedule_req,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    result = reschedule_appointment(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        request=reschedule_req,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n'
        '    if isinstance(result, Rejected):\n'
        '        result = None\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
    ),
    # 34. API Status - confirm reserved
    Mutation(
        TEST_STATUS,
        "test_confirm_reserved_appointment",
        API_APPOINTMENTS,
        '        target_status=AppointmentStatus(body.to_status),',
        '        target_status=AppointmentStatus.ATTENDED,',
    ),
    # 35. API Status - mark attended confirmed
    Mutation(
        TEST_STATUS,
        "test_mark_attended_confirmed_appointment_with_past_start",
        API_APPOINTMENTS,
        'def change_appointment_status_endpoint(\n'
        '    id: UUID,\n'
        '    body: StatusChangeInput,\n'
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CHANGE_STATUS)),\n'
        '    ],\n'
        '    request: Request,\n'
        '    session: Annotated[Session, Depends(get_db_session)],\n'
        ') -> AppointmentResponse:\n'
        '    settings: Settings = request.app.state.settings\n'
        '    now = datetime.now(UTC)',
        'def change_appointment_status_endpoint(\n'
        '    id: UUID,\n'
        '    body: StatusChangeInput,\n'
        '    permission: Annotated[\n'
        '        Permission,\n'
        '        Depends(require_permission(Resource.APPOINTMENT, Action.CHANGE_STATUS)),\n'
        '    ],\n'
        '    request: Request,\n'
        '    session: Annotated[Session, Depends(get_db_session)],\n'
        ') -> AppointmentResponse:\n'
        '    settings: Settings = request.app.state.settings\n'
        '    now = datetime(2000, 1, 1, tzinfo=UTC)',
    ),
    # 36. API Status - mark absent confirmed
    Mutation(
        TEST_STATUS,
        "test_mark_absent_confirmed_appointment_with_past_start",
        API_APPOINTMENTS,
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus.ATTENDED,\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
    ),
    # 37. API Status - mark attended before start returns 422
    Mutation(
        TEST_STATUS,
        "test_mark_attended_before_start_returns_422",
        API_APPOINTMENTS,
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise DomainRejectedError(result)',
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):\n'
        '        raise NotFoundError("Turno no encontrado.")',
    ),
    # 38. API Status - double sequential transition leaves single new entry
    Mutation(
        TEST_STATUS,
        "test_double_sequential_transition_leaves_single_new_entry",
        API_APPOINTMENTS,
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )',
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=False,\n'
        '    )',
    ),
    # 39. API Status - confirm cancelled returns 422
    Mutation(
        TEST_STATUS,
        "test_confirm_cancelled_appointment_returns_422",
        API_APPOINTMENTS,
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):',
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n'
        '    if isinstance(result, Rejected):\n'
        '        result = None\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    if isinstance(result, Rejected):',
    ),
    # 40. API Status - toStatus cancelado returns 400
    Mutation(
        TEST_STATUS,
        "test_to_status_cancelado_returns_400",
        API_ERRORS,
        '    return JSONResponse(status_code=400, content={"errors": error_items})',
        '    return JSONResponse(status_code=422, content={"errors": error_items})',
    ),
    # 41. API Status - toStatus reservado returns 400
    Mutation(
        TEST_STATUS,
        "test_to_status_reservado_returns_400",
        API_SCHEMAS,
        'class StatusChangeInput(BaseModel):\n'
        '    to_status: AllowedStatusChange = Field(alias="toStatus")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
        'class StatusChangeInput(BaseModel):\n'
        '    to_status: str = Field(alias="toStatus")\n\n'
        '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
    ),
    # 42. API Status - nonexistent returns 404
    Mutation(
        TEST_STATUS,
        "test_change_status_nonexistent_appointment_returns_404",
        API_APPOINTMENTS,
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,\n'
        '        now=now,\n'
        '        tz=tz,\n'
        '        auto_commit=True,\n'
        '    )\n\n'
        '    if result is None:\n'
        f'{FABRICATED_APPOINTMENT}',
    ),
    # 43. API Status - dentist foreign returns 403 from domain
    Mutation(
        TEST_STATUS,
        "test_dentist_changes_status_of_other_professional_returns_403_from_domain",
        API_APPOINTMENTS,
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=permission.actor,',
        '    result = change_appointment_status(\n'
        '        session=session,\n'
        '        appointment_id=id,\n'
        '        target_status=AppointmentStatus(body.to_status),\n'
        '        actor=type(permission.actor)(\n'
        '            user_id=permission.actor.user_id,\n'
        '            role=type(permission.actor.role).ADMINISTRADOR,\n'
        '        ),',
    ),
    # 44. API History - ascending with creation and changedByName
    Mutation(
        TEST_HISTORY,
        "test_history_ascending_with_creation_and_changed_by_name",
        API_APPOINTMENTS,
        '    history = get_appointment_history(session, id)\n'
        '    if history is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    return history',
        '    history = get_appointment_history(session, id)\n'
        '    if history is None:\n'
        '        raise NotFoundError("Turno no encontrado.")\n\n'
        '    return list(reversed(history))',
    ),
    # 45. API History - reschedule entry has to reservado and flat detail
    Mutation(
        TEST_HISTORY,
        "test_history_reschedule_entry_has_to_reservado_and_flat_detail",
        API_APPOINTMENTS,
        '    history = get_appointment_history(session, id)\n'
        '    if history is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    history = get_appointment_history(session, id)\n'
        '    if history is not None:\n'
        '        history = []\n'
        '    if history is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
    ),
    # 46. API History - nonexistent returns 404
    Mutation(
        TEST_HISTORY,
        "test_history_nonexistent_appointment_returns_404",
        API_APPOINTMENTS,
        '    appointment = AppointmentRepository(session).get_by_id(id)\n'
        '    if appointment is None:\n'
        '        raise NotFoundError("Turno no encontrado.")',
        '    appointment = AppointmentRepository(session).get_by_id(id)\n'
        '    if appointment is None:\n'
        '        return []',
    ),
    # 47. API History - dentist reads own returns 200
    Mutation(
        TEST_HISTORY,
        "test_dentist_reads_own_appointment_history_returns_200",
        API_APPOINTMENTS,
        '    if permission.scope is Scope.OWN:\n'
        '        ensure_own_professional(permission, appointment.professional_id)',
        '    if permission.scope is Scope.OWN:\n'
        '        ensure_own_professional(permission, uuid4())',
    ),
    # 48. API History - dentist reads other returns 403
    Mutation(
        TEST_HISTORY,
        "test_dentist_reads_other_professional_history_returns_403",
        API_APPOINTMENTS,
        '    if permission.scope is Scope.OWN:\n'
        '        ensure_own_professional(permission, appointment.professional_id)',
        '    if False and permission.scope is Scope.OWN:\n'
        '        ensure_own_professional(permission, appointment.professional_id)',
    ),
    # 49. API History - reception reads other returns 200
    Mutation(
        TEST_HISTORY,
        "test_reception_reads_other_professional_history_returns_200",
        API_APPOINTMENTS,
        '        Depends(require_permission(Resource.APPOINTMENT_HISTORY, Action.READ)),',
        '        Depends(require_permission(Resource.WORKING_HOURS, Action.UPDATE)),',
    ),
    # 50. API History - admin reads other returns 200
    Mutation(
        TEST_HISTORY,
        "test_admin_reads_other_professional_history_returns_200",
        API_APPOINTMENTS,
        '@router.get(\n'
        '    "/{id}/history",\n'
        '    status_code=status.HTTP_200_OK,\n'
        '    response_model=list[HistoryEntryResponse],',
        '@router.get(\n'
        '    "/{id}/history",\n'
        '    status_code=status.HTTP_403_FORBIDDEN,\n'
        '    response_model=list[HistoryEntryResponse],',
    ),
    # 51. API OpenAPI - lifecycle documentation
    Mutation(
        TEST_OPENAPI,
        "test_appointment_lifecycle_openapi_documentation",
        API_APPOINTMENTS,
        '@router.post(\n'
        '    "/{id}/reschedule",\n'
        '    status_code=status.HTTP_200_OK,\n'
        '    response_model=AppointmentResponse,\n'
        '    responses={\n'
        '        **violation_responses(409, 422),',
        '@router.post(\n'
        '    "/{id}/reschedule",\n'
        '    status_code=status.HTTP_200_OK,\n'
        '    response_model=AppointmentResponse,\n'
        '    responses={\n'
        '        **violation_responses(422),',
    ),
)


class MutationAbort(Exception):
    pass


class Report:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def write(self, text: str) -> None:
        self.stream.write(text.rstrip() + "\n")
        self.stream.flush()


def tree_sha256() -> str:
    hasher = hashlib.sha256()
    for root, _, files in os.walk(BACKEND / "app"):
        for name in sorted(files):
            if name.endswith(".py"):
                path = Path(root) / name
                hasher.update(path.relative_to(BACKEND).as_posix().encode())
                hasher.update(path.read_bytes())
    return hasher.hexdigest()


def apply_mutation(mutation: Mutation, content: str) -> str:
    """Aplica la mutacion respetando el final de linea del archivo (LF o CRLF)."""
    newline = "\r\n" if "\r\n" in content else "\n"
    original = mutation.original.replace("\n", newline)
    mutated = mutation.mutated.replace("\n", newline)
    count = content.count(original)
    if count != 1:
        raise MutationAbort(
            f"{mutation.test_name}: original presente {count} veces en {mutation.file}"
        )
    return content.replace(original, mutated, 1)


def check_definition(mutation: Mutation) -> None:
    target = REPO / mutation.file
    if not target.exists():
        raise MutationAbort(f"{mutation.test_name}: {mutation.file} no existe")
    raw_content = target.read_bytes().decode("utf-8")
    content = raw_content.replace("\r\n", "\n")
    count = content.count(mutation.original)
    if count == 0:
        raise MutationAbort(
            f"{mutation.test_name}: original no encontrado en {mutation.file}\n"
            f"Original buscado:\n{mutation.original}"
        )
    if count > 1:
        raise MutationAbort(
            f"{mutation.test_name}: original ambiguo ({count} veces) en {mutation.file}"
        )
    if mutation.original == mutation.mutated:
        raise MutationAbort(f"{mutation.test_name}: mutacion identica al original")
    if apply_mutation(mutation, raw_content) == raw_content:
        raise MutationAbort(f"{mutation.test_name}: la mutacion no cambia {mutation.file}")


def run_pytest(test_targets: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [
        PYTHON,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "--no-header",
        "--tb=short",
        *test_targets,
    ]
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
    }
    return subprocess.run(
        cmd,
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env=env,
        timeout=TIMEOUT_SECONDS,
    )


def invalid_reason(output: str) -> str | None:
    """Devuelve el motivo si el test no detecto la mutacion con una afirmacion propia."""
    name_error = INVALID_NAME_ERROR.search(output)
    if name_error:
        return f"la salida contiene {name_error.group(1)}"

    frame = ""
    for line in output.splitlines():
        frame_match = FRAME_LINE.match(line)
        if frame_match:
            frame = frame_match.group(1).replace("\\", "/")
            continue
        if not line.startswith("E   "):
            continue
        first_error = line.removeprefix("E   ").strip()
        if not frame.startswith("tests/"):
            return f"primer E fuera de tests/ ({frame}): {first_error}"
        if not TEST_DETECTION.match(first_error):
            return f"primer E no es una afirmacion del test: {first_error}"
        return None
    return "la salida no tiene ninguna linea E"


def run_mutation(mutation: Mutation, index: int, report: Report) -> tuple[bool, str | None]:
    target = REPO / mutation.file
    original_bytes = target.read_bytes()
    original_content = original_bytes.decode("utf-8")
    mutated_content = apply_mutation(mutation, original_content)
    if mutated_content == original_content:
        raise MutationAbort(f"{mutation.test_name}: la mutacion no cambia {mutation.file}")

    diff = "".join(
        difflib.unified_diff(
            original_content.splitlines(keepends=True),
            mutated_content.splitlines(keepends=True),
            fromfile=f"a/{mutation.file}",
            tofile=f"b/{mutation.file}",
            n=2,
        )
    ).replace("\r\n", "\n")

    report.write(SEPARATOR)
    report.write(f"[{index:02d}/{len(MUTATIONS)}] {mutation.test_name}")
    report.write(f"test: {mutation.node_id}")
    report.write("diff:")
    report.write(diff)

    target.write_text(mutated_content, encoding="utf-8", newline="\n")
    try:
        mutated_result = run_pytest([mutation.node_id])
    finally:
        target.write_bytes(original_bytes)

    report.write(f"--- salida mutada (codigo de salida {mutated_result.returncode}) ---")
    report.write(mutated_result.stdout + mutated_result.stderr)

    restored_result = run_pytest([mutation.node_id])
    if restored_result.returncode != 0:
        report.write("FATAL: el test no volvio a verde tras restaurar el archivo")
        report.write(restored_result.stdout + restored_result.stderr)
        raise MutationAbort(
            f"{mutation.test_name}: no volvio a verde tras restaurar {mutation.file}"
        )
    report.write("restaurado: test en verde")

    killed = mutated_result.returncode != 0
    reason = invalid_reason(mutated_result.stdout + mutated_result.stderr) if killed else None
    if reason:
        report.write(f"INVALIDA: {reason}")
    return killed, reason


def parse_mutations_txt() -> list[tuple[str, str, str, str, str]]:
    if not OUTPUT.exists():
        return []
    content = OUTPUT.read_text(encoding="utf-8")
    entries: list[tuple[str, str, str, str, str]] = []
    current_index: str | None = None
    current_name: str | None = None
    current_file: str | None = None
    diff_lines: list[str] = []
    in_diff = False
    in_output = False
    first_failure_line = ""

    for line in content.splitlines():
        if line.startswith("[") and "/" in line and "]" in line:
            m = re.match(r"\[(\d+)/\d+\]\s+(\S+)", line)
            if m:
                current_index = m.group(1)
                current_name = m.group(2)
                diff_lines = []
                in_diff = False
                in_output = False
                first_failure_line = ""
        elif line.startswith("--- a/"):
            current_file = line.removeprefix("--- a/").strip()
        elif line == "diff:":
            in_diff = True
        elif line.startswith("--- salida mutada"):
            in_diff = False
            in_output = True
        elif line.startswith("restaurado:"):
            in_output = False
            if current_index and current_name and current_file:
                mutation_desc = " ".join(
                    l.strip()
                    for l in diff_lines
                    if l.startswith(("-", "+")) and not l.startswith(("---", "+++"))
                )[:80]
                entries.append(
                    (
                        str(int(current_index)),
                        current_name,
                        current_file,
                        mutation_desc or "mutacion",
                        first_failure_line or "FAILED",
                    )
                )
        elif in_diff:
            diff_lines.append(line)
        elif in_output and not first_failure_line:
            if "FAILED" in line or "E   " in line or "AssertionError" in line:
                first_failure_line = line.strip()[:80]

    return entries


def update_verify_table() -> None:
    entries = parse_mutations_txt()
    if not entries:
        return
    rows = [
        f"| {idx} | `{name}` | `{file}` | `{mut}` | `{fail}` |"
        for idx, name, file, mut, fail in entries
    ]
    table = "\n".join(
        [
            "| # | Test | Archivo | Mutación | Primera línea del fallo |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )
    verify = VERIFY.read_text(encoding="utf-8")
    start = verify.find(TABLE_START)
    end = verify.find(TABLE_END)
    if start != -1 and end != -1:
        VERIFY.write_text(
            f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
            encoding="utf-8",
            newline="\n",
        )


def main() -> int:
    check_only = "--check" in sys.argv
    for mutation in MUTATIONS:
        check_definition(mutation)

    if check_only:
        print(f"Todas las {len(MUTATIONS)} mutaciones estan bien definidas.")
        return 0

    sha_before = tree_sha256()
    killed: list[str] = []
    survived: list[str] = []
    invalid: list[str] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        report = Report(stream)
        report.write("Salida generada por docs/evidencias/mutaciones-C-23.py. No editar a mano.")
        report.write(f"SHA-256 de backend/app antes: {sha_before}")
        baseline = run_pytest([mutation.node_id for mutation in MUTATIONS])
        report.write(f"--- linea de base, sin mutaciones (codigo de salida {baseline.returncode}) ---")
        report.write(baseline.stdout + baseline.stderr)
        if baseline.returncode != 0:
            raise MutationAbort("Los tests no estan en verde antes de mutar")

        for index, mutation in enumerate(MUTATIONS, start=1):
            print(f"[{index:02d}/{len(MUTATIONS)}] {mutation.test_name}", flush=True)
            was_killed, reason = run_mutation(mutation, index, report)
            if reason:
                invalid.append(f"{mutation.test_name}: {reason}")
                print(f"    INVALIDA: {reason}", flush=True)
            elif was_killed:
                killed.append(mutation.test_name)
            else:
                survived.append(mutation.test_name)
                print("    NO hizo fallar su test", flush=True)

        sha_after = tree_sha256()
        same = sha_before == sha_after
        summary = [
            SEPARATOR,
            "RESUMEN",
            f"mutaciones que hicieron fallar su test: {len(killed)}",
            f"mutaciones que NO lo hicieron fallar: {len(survived)}",
            *[f"  - {name}" for name in survived],
            f"mutaciones inválidas: {len(invalid)}",
            *[f"  - {entry}" for entry in invalid],
            f"SHA-256 de backend/app despues: {sha_after}",
            f"SHA-256 sin cambios: {'si' if same else 'NO'}",
        ]
        report.write("\n".join(summary))

    print("\n".join(summary))
    update_verify_table()
    return 0 if same and not survived and not invalid else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MutationAbort as error:
        print(f"ABORTADO: {error}", file=sys.stderr)
        sys.exit(2)
