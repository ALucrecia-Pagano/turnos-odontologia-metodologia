"""Verificacion por mutacion, reproducible, de los tests de C-24.

Uso, desde backend/:

    python ../docs/evidencias/mutaciones-C-24.py [--check]

Cada mutacion es (archivo, texto_original, texto_mutado) sobre codigo de produccion.
Por cada una: comprueba que el original aparezca exactamente una vez, aplica la
mutacion, corre solo su test, restaura el archivo en un finally y vuelve a correr el test.

Con --check solo ejecuta check_definition sobre todas las mutaciones.
Solo toca la base <POSTGRES_DB>_test. Genera mutaciones-C-24.txt y regenera la tabla de
verify-C-24.md leyendo ese .txt. Termina con codigo 0 solo si todas las mutaciones
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
OUTPUT = EVIDENCE / "mutaciones-C-24.txt"
VERIFY = EVIDENCE / "verify-C-24.md"
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


TEST_SCHEMAS = "tests/api/test_agenda_schemas.py"
TEST_RESPONSE_SCHEMAS = "tests/api/test_agenda_response_schemas.py"
TEST_QUERY_ERRORS = "tests/api/test_agenda_query_errors.py"
TEST_REPOSITORIES = "tests/integration/test_agenda_repositories.py"
TEST_SERVICE = "tests/integration/test_agenda_service.py"
TEST_AGENDA = "tests/integration/test_api_agenda.py"
TEST_MIDNIGHT = "tests/integration/test_api_agenda_midnight.py"
TEST_VALIDATION = "tests/integration/test_api_agenda_validation.py"
TEST_DETAIL = "tests/integration/test_api_appointment_detail.py"
TEST_OPENAPI = "tests/integration/test_agenda_openapi.py"

API_SCHEMAS = "backend/app/api/schemas.py"
API_ERRORS = "backend/app/api/errors.py"
API_AGENDA = "backend/app/api/agenda.py"
API_APPOINTMENTS = "backend/app/api/appointments.py"
API_MAIN = "backend/app/main.py"
REPO_APPOINTMENT = "backend/app/repositories/appointment.py"
REPO_BLOCKS = "backend/app/repositories/blocks.py"
REPO_WORKING_HOURS = "backend/app/repositories/working_hours.py"
SERVICE_AGENDA = "backend/app/services/agenda.py"


def L(*lines: str) -> str:
    return "\n".join(lines)


FROM_FIELD = '        alias="from", description="Fecha local inicial en formato AAAA-MM-DD."'
TO_FIELD = L(
    '        alias="to",',
    '        description="Fecha local final inclusiva en formato AAAA-MM-DD; máximo 31 días desde from.",',
)
PROF_FIELD = L(
    '        alias="professionalId",',
    '        description="Filtra turnos, horarios y bloqueos de un profesional.",',
)
CHAIR_FIELD = L(
    '        alias="chairId",',
    '        description="Filtra solo los turnos de un sillón.",',
)
EXTRA_FORBID = L(
    '    model_config = ConfigDict(populate_by_name=True, extra="forbid")',
    '',
    '    @field_validator("from_date", "to_date", mode="before")',
)
EXTRA_ALLOW = EXTRA_FORBID.replace('extra="forbid"', 'extra="ignore"')
MAX_DAYS = "MAX_AGENDA_DAYS: Final = 31"
DATE_MSG = '"invalid_date_format", "La fecha debe tener formato AAAA-MM-DD."'
RANGE_LEN_CHECK = "if (self.to_date - self.from_date).days + 1 > MAX_AGENDA_DAYS:"
AGENDA_OVERLAP = L(
    "            AppointmentModel.start_at < end_at,",
    "            AppointmentModel.end_at > start_at,",
    "        )",
    "        if professional_id is not None:",
)
PROF_FILTER_LINE = "            stmt = stmt.where(AppointmentModel.professional_id == professional_id)"
CHAIR_FILTER_LINE = "            stmt = stmt.where(AppointmentModel.chair_id == chair_id)"
BLOCK_OVERLAP = L(
    "            BlockModel.start_at < end_at,",
    "            BlockModel.end_at > start_at,",
)
BLOCK_ORDER_RETURN = L(
    "        stmt = stmt.order_by(BlockModel.start_at, BlockModel.id)",
    "        return tuple(self._to_domain(row) for row in self._session.scalars(stmt).all())",
)
PROFESSIONAL_AND_CHAIR_ARGS = L(
    "        params.professional_id,",
    "        params.chair_id,",
)
HOURS_BLOCK = L(
    "    working_hours = (",
    "        hours_repo.list()",
    "        if professional_id is None",
    "        else hours_repo.list_by_professional(professional_id)",
    "    )",
)
DETAIL_TAIL = L(
    '        raise NotFoundError("Turno no encontrado.")',
    "    return to_agenda_appointment_response(appointment)",
)
DETAIL_RESPONSES = L(
    "    response_model=AgendaAppointmentResponse,",
    "    responses={",
    '        **not_found_responses("Turno"),',
    "        **permission_responses(),",
    "    },",
    ")",
    "def get_appointment_endpoint(",
)

MUTATIONS: tuple[Mutation, ...] = (
    # --- Esquema AgendaQuery (tests/api/test_agenda_schemas.py) ---
    Mutation(TEST_SCHEMAS, "test_agenda_query_parses_dates_and_aliases", API_SCHEMAS,
             FROM_FIELD, FROM_FIELD.replace('alias="from"', 'alias="desde"')),
    Mutation(TEST_SCHEMAS, "test_agenda_query_accepts_single_day_and_31_day_ranges", API_SCHEMAS,
             MAX_DAYS, "MAX_AGENDA_DAYS: Final = 30"),
    Mutation(TEST_SCHEMAS, "test_agenda_query_rejects_range_longer_than_31_days", API_SCHEMAS,
             RANGE_LEN_CHECK, "if (self.to_date - self.from_date).days > MAX_AGENDA_DAYS:"),
    Mutation(TEST_SCHEMAS, "test_agenda_query_rejects_to_before_from", API_SCHEMAS,
             "if self.to_date < self.from_date:", "if False and self.to_date < self.from_date:"),
    Mutation(TEST_SCHEMAS, "test_agenda_query_rejects_invalid_date_format", API_SCHEMAS,
             DATE_MSG, '"invalid_date_format", "Fecha inválida."'),
    Mutation(TEST_SCHEMAS, "test_agenda_query_requires_from_and_to", API_SCHEMAS,
             FROM_FIELD, FROM_FIELD.replace('alias="from"', 'default=date.max, alias="from"')),
    Mutation(TEST_SCHEMAS, "test_agenda_query_professional_and_chair_ids_are_optional_uuids", API_SCHEMAS,
             L("        default=None,", PROF_FIELD),
             L("        default=None,", PROF_FIELD.replace('"professionalId"', '"professionalID"'))),
    Mutation(TEST_SCHEMAS, "test_agenda_query_forbids_extra_parameters", API_SCHEMAS,
             EXTRA_FORBID, EXTRA_ALLOW),
    Mutation(TEST_SCHEMAS, "test_agenda_query_model_dump_by_alias", API_SCHEMAS,
             CHAIR_FIELD, CHAIR_FIELD.replace('"chairId"', '"chair"')),
    # --- Esquemas de respuesta ---
    Mutation(TEST_RESPONSE_SCHEMAS, "test_agenda_appointment_response_serializes_names_in_camel_case", API_SCHEMAS,
             '    professional_name: str = Field(serialization_alias="professionalName")',
             '    professional_name: str = Field(serialization_alias="professionalNm")'),
    Mutation(TEST_RESPONSE_SCHEMAS, "test_agenda_working_hours_response_keeps_hh_mm_including_24_00", API_SCHEMAS,
             L("    weekday: int", "    start: str", "    end: str", "",
               "    model_config = ConfigDict(populate_by_name=True)", "", "", "class AgendaResponse(BaseModel):"),
             L("    weekday: int", "    start: str", '    end: str = Field(serialization_alias="finish")', "",
               "    model_config = ConfigDict(populate_by_name=True)", "", "", "class AgendaResponse(BaseModel):")),
    Mutation(TEST_RESPONSE_SCHEMAS, "test_agenda_response_envelope_uses_from_to_and_timezone", API_SCHEMAS,
             '    from_date: date = Field(serialization_alias="from")',
             '    from_date: date = Field(serialization_alias="desde")'),
    # --- Mensajes 400 ---
    Mutation(TEST_QUERY_ERRORS, "test_agenda_query_errors_return_400_with_spanish_messages", API_ERRORS,
             '    "invalid_range_length": "El rango no puede superar los 31 días.",',
             '    "invalid_range_length": "El rango es demasiado largo.",'),
    # --- Repositorios ---
    Mutation(TEST_REPOSITORIES, "test_list_for_agenda_in_range_returns_appointments_with_names", REPO_APPOINTMENT,
             L("        professional_name=professional_name,", "        chair_name=chair_name,",
               "        service_name=service_name,"),
             L("        professional_name=professional_name,", "        chair_name=service_name,",
               "        service_name=chair_name,")),
    Mutation(TEST_REPOSITORIES, "test_list_for_agenda_in_range_uses_half_open_overlap", REPO_APPOINTMENT,
             AGENDA_OVERLAP, AGENDA_OVERLAP.replace("end_at > start_at", "end_at >= start_at")),
    Mutation(TEST_REPOSITORIES, "test_list_for_agenda_in_range_combines_optional_filters", REPO_APPOINTMENT,
             CHAIR_FILTER_LINE, CHAIR_FILTER_LINE.replace("== chair_id", "!= chair_id")),
    Mutation(TEST_REPOSITORIES, "test_list_for_agenda_in_range_orders_by_start_then_id", REPO_APPOINTMENT,
             L("        stmt = stmt.order_by(AppointmentModel.start_at, AppointmentModel.id)",
               "        return tuple(_to_with_names(row)"),
             L("        stmt = stmt.order_by(AppointmentModel.start_at, AppointmentModel.id.desc())",
               "        return tuple(_to_with_names(row)")),
    Mutation(TEST_REPOSITORIES, "test_list_for_agenda_in_range_runs_a_single_query", REPO_APPOINTMENT,
             "        return tuple(_to_with_names(row) for row in self._session.execute(stmt).all())",
             L("        rows = self._session.execute(stmt).all()",
               "        self._session.execute(stmt).all()",
               "        return tuple(_to_with_names(row) for row in rows)")),
    Mutation(TEST_REPOSITORIES, "test_get_with_names_returns_enriched_row_or_none", REPO_APPOINTMENT,
             "_agenda_select().where(AppointmentModel.id == identifier)",
             "_agenda_select().where(AppointmentModel.id != identifier)"),
    Mutation(TEST_REPOSITORIES, "test_block_list_in_range_uses_half_open_overlap_and_midnight_crossing", REPO_BLOCKS,
             BLOCK_OVERLAP, BLOCK_OVERLAP.replace("end_at > start_at", "end_at >= start_at")),
    Mutation(TEST_REPOSITORIES, "test_block_list_in_range_filters_by_optional_professional", REPO_BLOCKS,
             L("            stmt = stmt.where(BlockModel.professional_id == professional_id)", BLOCK_ORDER_RETURN),
             L("            stmt = stmt.where(BlockModel.professional_id != professional_id)", BLOCK_ORDER_RETURN)),
    Mutation(TEST_REPOSITORIES, "test_block_list_in_range_orders_by_start_then_id", REPO_BLOCKS,
             BLOCK_ORDER_RETURN, BLOCK_ORDER_RETURN.replace("BlockModel.id)", "BlockModel.id.desc())")),
    # --- Servicio ---
    Mutation(TEST_SERVICE, "test_get_agenda_maps_appointments_with_names_and_utc_instants", SERVICE_AGENDA,
             "        chair_name=row.chair_name,", "        chair_name=row.service_name,"),
    Mutation(TEST_SERVICE, "test_get_agenda_returns_envelope_with_requested_dates_and_timezone", SERVICE_AGENDA,
             "        timezone=tz.key,", '        timezone="UTC",'),
    Mutation(TEST_SERVICE, "test_get_agenda_window_uses_local_midnights_and_inclusive_to", SERVICE_AGENDA,
             "window_end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=tz)",
             "window_end = datetime.combine(to_date, time.min, tzinfo=tz)"),
    Mutation(TEST_SERVICE, "test_get_agenda_filters_working_hours_and_blocks_by_professional_but_not_by_chair", SERVICE_AGENDA,
             HOURS_BLOCK, "    working_hours = hours_repo.list()"),
    Mutation(TEST_SERVICE, "test_get_agenda_applies_professional_and_chair_filters_to_appointments", SERVICE_AGENDA,
             "        window_start, window_end, professional_id=professional_id, chair_id=chair_id",
             "        window_start, window_end, professional_id=professional_id, chair_id=None"),
    Mutation(TEST_SERVICE, "test_get_agenda_runs_three_queries_without_n_plus_one", SERVICE_AGENDA,
             "    hours_repo = WorkingHoursRepository(session)\n",
             "    hours_repo = WorkingHoursRepository(session)\n    hours_repo.list()\n"),
    Mutation(TEST_SERVICE, "test_get_agenda_does_not_commit_or_rollback", SERVICE_AGENDA,
             "    return Agenda(\n", "    session.commit()\n    return Agenda(\n"),
    Mutation(TEST_SERVICE, "test_get_agenda_appointment_returns_mapped_appointment_or_none", SERVICE_AGENDA,
             "        status=appointment.status.value,", '        status="reservado",'),
    # --- API de la agenda ---
    Mutation(TEST_AGENDA, "test_agenda_for_one_day_returns_complete_envelope", API_AGENDA,
             "        timezone=agenda.timezone,", '        timezone="UTC",'),
    Mutation(TEST_AGENDA, "test_agenda_for_a_week_returns_the_appointments_of_the_range", API_AGENDA,
             "        to_date=agenda.to_date,", "        to_date=agenda.from_date,"),
    Mutation(TEST_AGENDA, "test_agenda_of_eight_days_crosses_two_weeks_in_order", SERVICE_AGENDA,
             "appointments=tuple(_to_agenda_appointment(row) for row in rows),",
             "appointments=tuple(_to_agenda_appointment(row) for row in reversed(rows)),"),
    Mutation(TEST_AGENDA, "test_agenda_of_31_days_crosses_months", API_SCHEMAS,
             MAX_DAYS, "MAX_AGENDA_DAYS: Final = 30"),
    Mutation(TEST_AGENDA, "test_agenda_filter_by_professional_returns_their_appointments", API_AGENDA,
             PROFESSIONAL_AND_CHAIR_ARGS, PROFESSIONAL_AND_CHAIR_ARGS.replace("params.professional_id", "None")),
    Mutation(TEST_AGENDA, "test_agenda_filter_by_chair_returns_their_appointments", API_AGENDA,
             L("        params.chair_id,", "        ZoneInfo(settings.app_timezone),"),
             L("        None,", "        ZoneInfo(settings.app_timezone),")),
    Mutation(TEST_AGENDA, "test_agenda_professional_and_chair_filters_combine", REPO_APPOINTMENT,
             PROF_FILTER_LINE, PROF_FILTER_LINE.replace("== professional_id", "!= professional_id")),
    Mutation(TEST_AGENDA, "test_agenda_unknown_professional_returns_empty_lists", REPO_APPOINTMENT,
             L("        if professional_id is not None:", PROF_FILTER_LINE),
             L("        if False:", PROF_FILTER_LINE)),
    Mutation(TEST_AGENDA, "test_agenda_unknown_chair_empties_appointments_but_not_hours_or_blocks", REPO_APPOINTMENT,
             L("        if chair_id is not None:", CHAIR_FILTER_LINE),
             L("        if False:", CHAIR_FILTER_LINE)),
    Mutation(TEST_AGENDA, "test_agenda_chair_filter_does_not_filter_hours_or_blocks", SERVICE_AGENDA,
             L("        hours_repo.list()", "        if professional_id is None"),
             L("        hours_repo.list()", "        if professional_id is None and chair_id is None")),
    Mutation(TEST_AGENDA, "test_agenda_dentist_sees_appointments_of_another_professional", API_AGENDA,
             PROFESSIONAL_AND_CHAIR_ARGS,
             PROFESSIONAL_AND_CHAIR_ARGS.replace(
                 "params.professional_id,", "params.professional_id or permission.actor.professional_id,"
             )),
    Mutation(TEST_AGENDA, "test_agenda_working_hours_template_includes_all_professionals", API_AGENDA,
             "            for slot in agenda.working_hours\n", "            for slot in agenda.working_hours[:1]\n"),
    Mutation(TEST_AGENDA, "test_agenda_professional_filter_also_filters_working_hours", REPO_WORKING_HOURS,
             L("            .where(WorkingHoursModel.professional_id == professional_id)",
               "            .order_by(WorkingHoursModel.weekday, WorkingHoursModel.start_minute)"),
             L("            .where(WorkingHoursModel.professional_id != professional_id)",
               "            .order_by(WorkingHoursModel.weekday, WorkingHoursModel.start_minute)")),
    Mutation(TEST_AGENDA, "test_agenda_block_inside_range_is_returned_with_reason", API_AGENDA,
             "                reason=block.reason,", "                reason=None,"),
    Mutation(TEST_AGENDA, "test_agenda_block_starting_before_the_range_is_included", REPO_BLOCKS,
             BLOCK_OVERLAP, BLOCK_OVERLAP.replace("BlockModel.end_at > start_at", "BlockModel.start_at >= start_at")),
    Mutation(TEST_AGENDA, "test_agenda_professional_filter_also_filters_blocks", SERVICE_AGENDA,
             L("        window_start, window_end, professional_id=professional_id", "    )"),
             L("        window_start, window_end, professional_id=None", "    )")),
    Mutation(TEST_AGENDA, "test_agenda_includes_cancelled_appointments_with_their_status", REPO_APPOINTMENT,
             "        status=AppointmentStatus(row.status),", "        status=AppointmentStatus.RESERVED,"),
    Mutation(TEST_AGENDA, "test_agenda_orders_appointments_blocks_and_working_hours", SERVICE_AGENDA,
             "        blocks=blocks,", "        blocks=tuple(reversed(blocks)),"),
    Mutation(TEST_AGENDA, "test_agenda_uses_one_query_per_resource_without_n_plus_one", REPO_BLOCKS,
             "        return tuple(self._to_domain(row) for row in self._session.scalars(stmt).all())",
             L("        rows = self._session.scalars(stmt).all()",
               "        self._session.scalars(stmt).all()",
               "        return tuple(self._to_domain(row) for row in rows)")),
    # --- Borde de medianoche ---
    Mutation(TEST_MIDNIGHT, "test_appointment_ending_at_midnight_appears_only_on_its_own_day", REPO_APPOINTMENT,
             AGENDA_OVERLAP, AGENDA_OVERLAP.replace("start_at < end_at", "start_at <= end_at")),
    Mutation(TEST_MIDNIGHT, "test_appointment_starting_at_midnight_appears_only_on_its_own_day", REPO_APPOINTMENT,
             AGENDA_OVERLAP, AGENDA_OVERLAP.replace("end_at > start_at", "end_at >= start_at")),
    Mutation(TEST_MIDNIGHT, "test_agenda_shows_the_replaced_hours_with_24_00_and_00_00", API_AGENDA,
             '                end=f"{slot.end_minute // 60:02d}:{slot.end_minute % 60:02d}",',
             '                end=f"{slot.end_minute // 60 % 24:02d}:{slot.end_minute % 60:02d}",'),
    Mutation(TEST_MIDNIGHT, "test_block_crossing_midnight_appears_on_both_days", REPO_BLOCKS,
             BLOCK_OVERLAP, BLOCK_OVERLAP.replace("BlockModel.end_at > start_at", "BlockModel.start_at >= start_at")),
    # --- Validación 400/401 ---
    Mutation(TEST_VALIDATION, "test_missing_from_returns_400", API_SCHEMAS,
             FROM_FIELD, FROM_FIELD.replace('alias="from"', 'default=date.max, alias="from"')),
    Mutation(TEST_VALIDATION, "test_missing_to_returns_400", API_SCHEMAS,
             TO_FIELD, TO_FIELD.replace('alias="to",', 'default=date.min, alias="to",')),
    Mutation(TEST_VALIDATION, "test_invalid_date_format_returns_400", API_ERRORS,
             '    "invalid_date_format": "La fecha debe tener formato AAAA-MM-DD.",',
             '    "invalid_date_format": "Fecha inválida.",'),
    Mutation(TEST_VALIDATION, "test_to_before_from_returns_400", API_ERRORS,
             '    "invalid_range_order": "La fecha final no puede ser anterior a la inicial.",',
             '    "invalid_range_order": "El orden de las fechas es inválido.",'),
    Mutation(TEST_VALIDATION, "test_range_longer_than_31_days_returns_400", API_SCHEMAS,
             MAX_DAYS, "MAX_AGENDA_DAYS: Final = 32"),
    Mutation(TEST_VALIDATION, "test_malformed_professional_id_returns_400", API_SCHEMAS,
             PROF_FIELD, PROF_FIELD.replace('"professionalId"', '"professional"')),
    Mutation(TEST_VALIDATION, "test_malformed_chair_id_returns_400", API_SCHEMAS,
             CHAIR_FIELD, CHAIR_FIELD.replace('"chairId"', '"sillon"')),
    Mutation(TEST_VALIDATION, "test_unknown_query_parameter_returns_400", API_SCHEMAS,
             EXTRA_FORBID, EXTRA_ALLOW),
    Mutation(TEST_VALIDATION, "test_agenda_without_token_returns_401", API_MAIN,
             "protected_router.include_router(agenda_router)", "pass"),
    # --- Detalle de un turno ---
    Mutation(TEST_DETAIL, "test_detail_returns_the_enriched_appointment", API_AGENDA,
             "        chair_name=item.chair_name,", "        chair_name=item.service_name,"),
    Mutation(TEST_DETAIL, "test_detail_shows_the_current_status_of_a_cancelled_appointment", SERVICE_AGENDA,
             "        status=appointment.status.value,", '        status="confirmado",'),
    Mutation(TEST_DETAIL, "test_detail_of_unknown_appointment_returns_404", API_APPOINTMENTS,
             L("    appointment = get_agenda_appointment(session, id)", "    if appointment is None:",
               '        raise NotFoundError("Turno no encontrado.")'),
             L("    appointment = get_agenda_appointment(session, id)", "    if appointment is None:",
               '        raise NotFoundError("Turno inexistente.")')),
    Mutation(TEST_DETAIL, "test_detail_with_malformed_uuid_returns_400", API_APPOINTMENTS,
             L("@router.get(", '    "/{id}",', "    status_code=status.HTTP_200_OK,",
               "    response_model=AgendaAppointmentResponse,"),
             L("@router.get(", '    "/{appointment_id}",', "    status_code=status.HTTP_200_OK,",
               "    response_model=AgendaAppointmentResponse,")),
    Mutation(TEST_DETAIL, "test_detail_without_token_returns_401", API_MAIN,
             "protected_router.include_router(appointments_router)", "pass"),
    Mutation(TEST_DETAIL, "test_dentist_reads_the_detail_of_another_professionals_appointment", API_APPOINTMENTS,
             DETAIL_TAIL,
             L('        raise NotFoundError("Turno no encontrado.")',
               "    if permission.actor.professional_id not in (None, appointment.professional_id):",
               '        raise NotFoundError("Turno no encontrado.")',
               "    return to_agenda_appointment_response(appointment)")),
    # --- OpenAPI ---
    Mutation(TEST_OPENAPI, "test_agenda_openapi_documents_parameters_responses_and_models", API_AGENDA,
             "    responses={**permission_responses()},", "    responses={},"),
    Mutation(TEST_OPENAPI, "test_appointment_detail_openapi_documents_responses_and_model", API_APPOINTMENTS,
             DETAIL_RESPONSES,
             L("    response_model=AgendaAppointmentResponse,", "    responses={**permission_responses()},", ")",
               "def get_appointment_endpoint(")),
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
        report.write("Salida generada por docs/evidencias/mutaciones-C-24.py. No editar a mano.")
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
