# Verificación de C-24 — api-consulta-de-agenda

## Resultado

Todos los números salen de los archivos enlazados, generados por redirección.

- Tareas: 27/27 en [tasks.md](../../openspec/changes/api-consulta-de-agenda/tasks.md).
- Precondición (C3): [precondicion-C-24.txt](precondicion-C-24.txt); C-21, C-22 y C-23 archivados.
- Línea de base: [baseline-C-24.txt](baseline-C-24.txt) (882 passed, 467 deselected; 467 passed en integración; mypy en 170 archivos).
- Suite por defecto: [pytest-C-24.txt](pytest-C-24.txt).
- Integración: [pytest-integration-C-24.txt](pytest-integration-C-24.txt).
- `mypy --strict app tests`: [mypy-C-24.txt](mypy-C-24.txt).
- Mutaciones: [mutaciones-C-24.txt](mutaciones-C-24.txt) (70/70 hicieron fallar su test; mutaciones inválidas: 0; SHA-256 de `backend/app` intacto).
- Trazabilidad: [trazabilidad-C-24.txt](trazabilidad-C-24.txt) (34 escenarios, 0 problemas).
- Validación OpenSpec: [validate-C-24.txt](validate-C-24.txt).
- Rojos (TDD): carpeta [red-C-24/](red-C-24/).

## Desvíos

- Los escenarios de L+30 (31 días) agregan por SQL un horario del miércoles para P1, porque L+30 cae miércoles y el horario demo es solo del lunes.
- `recepcion` no puede crear bloqueos (matriz C-19): los tests crean los bloqueos con el token de administrador.
- Los nombres de P1 y P2 se renombran a los de `demo_data.py` en el fixture, porque `auth_support` los crea como "Dra. Ficticia Uno"/"Dr. Ficticio Dos".
- Las tareas 4.2, 4.3 y 4.4 pasaron de entrada o ya tenían la ruta: se registraron `4.2-mutacion.txt` y `4.3-mutacion.txt` en `red-C-24/`.
- Se agregaron descripciones a los parámetros de `AgendaQuery` para documentar que `to` es inclusivo (test de OpenAPI en rojo antes).
- Con SQLAlchemy 2.1 los tipos de `select` son variádicos (`Select[A, str, ...]`).

## Mutaciones

<!-- mutaciones:inicio -->
| # | Test | Archivo | Mutación | Primera línea del fallo |
|---|---|---|---|---|
| 1 | `test_agenda_query_parses_dates_and_aliases` | `backend/app/api/schemas.py` | `-        alias="from", description="Fecha local inicial en formato AAAA-MM-DD." ` | `E   pydantic_core._pydantic_core.ValidationError: 2 validation errors for Agenda` |
| 2 | `test_agenda_query_accepts_single_day_and_31_day_ranges` | `backend/app/api/schemas.py` | `-MAX_AGENDA_DAYS: Final = 31 +MAX_AGENDA_DAYS: Final = 30` | `E   pydantic_core._pydantic_core.ValidationError: 1 validation error for AgendaQ` |
| 3 | `test_agenda_query_rejects_range_longer_than_31_days` | `backend/app/api/schemas.py` | `-        if (self.to_date - self.from_date).days + 1 > MAX_AGENDA_DAYS: +       ` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 4 | `test_agenda_query_rejects_to_before_from` | `backend/app/api/schemas.py` | `-        if self.to_date < self.from_date: +        if False and self.to_date < ` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 5 | `test_agenda_query_rejects_invalid_date_format` | `backend/app/api/schemas.py` | `-            "invalid_date_format", "La fecha debe tener formato AAAA-MM-DD." + ` | `E   AssertionError: assert 'Fecha invÃ¡lida.' == 'La fecha deb...o AAAA-MM-DD.'` |
| 6 | `test_agenda_query_requires_from_and_to` | `backend/app/api/schemas.py` | `-        alias="from", description="Fecha local inicial en formato AAAA-MM-DD." ` | `E   AssertionError: assert [('to', 'missing')] == [('from', 'mi...', 'missing')]` |
| 7 | `test_agenda_query_professional_and_chair_ids_are_optional_uuids` | `backend/app/api/schemas.py` | `-        alias="professionalId", +        alias="professionalID",` | `E   pydantic_core._pydantic_core.ValidationError: 1 validation error for AgendaQ` |
| 8 | `test_agenda_query_forbids_extra_parameters` | `backend/app/api/schemas.py` | `-    model_config = ConfigDict(populate_by_name=True, extra="forbid") +    model` | `E   Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| 9 | `test_agenda_query_model_dump_by_alias` | `backend/app/api/schemas.py` | `-        alias="chairId", +        alias="chair",` | `E   AssertionError: assert {'chair': Non...(2026, 12, 8)} == {'chairId': N...(20` |
| 10 | `test_agenda_appointment_response_serializes_names_in_camel_case` | `backend/app/api/schemas.py` | `-    professional_name: str = Field(serialization_alias="professionalName") +   ` | `E   AssertionError: assert {'chairId': '...00000a1', ...} == {'chairId': '...000` |
| 11 | `test_agenda_working_hours_response_keeps_hh_mm_including_24_00` | `backend/app/api/schemas.py` | `-    end: str +    end: str = Field(serialization_alias="finish")` | `E   AssertionError: assert {'finish': '2... 'weekday': 1} == {'end': '24:0... 'w` |
| 12 | `test_agenda_response_envelope_uses_from_to_and_timezone` | `backend/app/api/schemas.py` | `-    from_date: date = Field(serialization_alias="from") +    from_date: date = ` | `E   AssertionError: assert ['desde', 'to...rs', 'blocks'] == ['from', 'to'...rs'` |
| 13 | `test_agenda_query_errors_return_400_with_spanish_messages` | `backend/app/api/errors.py` | `-    "invalid_range_length": "El rango no puede superar los 31 días.", +    "inv` | `E   AssertionError: {'from': '2026-12-07', 'to': '2027-01-07'}` |
| 14 | `test_list_for_agenda_in_range_returns_appointments_with_names` | `backend/app/repositories/appointment.py` | `-        chair_name=chair_name, -        service_name=service_name, +        cha` | `E   AssertionError: assert 'Servicio Agenda' == 'SillÃ³n Agenda A'` |
| 15 | `test_list_for_agenda_in_range_uses_half_open_overlap` | `backend/app/repositories/appointment.py` | `-            AppointmentModel.end_at > start_at, +            AppointmentModel.e` | `E   AssertionError: assert [UUID('000000...00000001f45')] == [UUID('000000...000` |
| 16 | `test_list_for_agenda_in_range_combines_optional_filters` | `backend/app/repositories/appointment.py` | `-            stmt = stmt.where(AppointmentModel.chair_id == chair_id) +         ` | `E   AssertionError: assert [UUID('000000...00000001f42')] == [UUID('000000...000` |
| 17 | `test_list_for_agenda_in_range_orders_by_start_then_id` | `backend/app/repositories/appointment.py` | `-        stmt = stmt.order_by(AppointmentModel.start_at, AppointmentModel.id) + ` | `E   AssertionError: assert [UUID('000000...00000001f43')] == [UUID('000000...000` |
| 18 | `test_list_for_agenda_in_range_runs_a_single_query` | `backend/app/repositories/appointment.py` | `-        return tuple(_to_with_names(row) for row in self._session.execute(stmt)` | `E   AssertionError: assert 2 == 1` |
| 19 | `test_get_with_names_returns_enriched_row_or_none` | `backend/app/repositories/appointment.py` | `-            _agenda_select().where(AppointmentModel.id == identifier) +        ` | `E   assert None is not None` |
| 20 | `test_block_list_in_range_uses_half_open_overlap_and_midnight_crossing` | `backend/app/repositories/blocks.py` | `-            BlockModel.end_at > start_at, +            BlockModel.end_at >= sta` | `E   AssertionError: assert [UUID('000000...00000001f44')] == [UUID('000000...000` |
| 21 | `test_block_list_in_range_filters_by_optional_professional` | `backend/app/repositories/blocks.py` | `-            stmt = stmt.where(BlockModel.professional_id == professional_id) + ` | `E   AssertionError: assert [UUID('000000...00000001f41')] == [UUID('000000...000` |
| 22 | `test_block_list_in_range_orders_by_start_then_id` | `backend/app/repositories/blocks.py` | `-        stmt = stmt.order_by(BlockModel.start_at, BlockModel.id) +        stmt ` | `E   AssertionError: assert [UUID('000000...00000001f43')] == [UUID('000000...000` |
| 23 | `test_get_agenda_maps_appointments_with_names_and_utc_instants` | `backend/app/services/agenda.py` | `-        chair_name=row.chair_name, +        chair_name=row.service_name,` | `E   AssertionError: assert 'Servicio Agenda' == 'SillÃ³n Agenda A'` |
| 24 | `test_get_agenda_returns_envelope_with_requested_dates_and_timezone` | `backend/app/services/agenda.py` | `-        timezone=tz.key, +        timezone="UTC",` | `E   AssertionError: assert 'UTC' == 'America/Arge.../Buenos_Aires'` |
| 25 | `test_get_agenda_window_uses_local_midnights_and_inclusive_to` | `backend/app/services/agenda.py` | `-    window_end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo` | `E   AssertionError: assert [] == [UUID('000000...00000001f41')]` |
| 26 | `test_get_agenda_filters_working_hours_and_blocks_by_professional_but_not_by_chair` | `backend/app/services/agenda.py` | `-    working_hours = ( -        hours_repo.list() -        if professional_id is` | `E   AssertionError: assert {UUID('000000...00000001b5a')} == {UUID('000000...000` |
| 27 | `test_get_agenda_applies_professional_and_chair_filters_to_appointments` | `backend/app/services/agenda.py` | `-        window_start, window_end, professional_id=professional_id, chair_id=cha` | `E   AssertionError: assert [UUID('000000...00000001f43')] == [UUID('000000...000` |
| 28 | `test_get_agenda_runs_three_queries_without_n_plus_one` | `backend/app/services/agenda.py` | `+    hours_repo.list()` | `E   AssertionError: assert 4 == 3` |
| 29 | `test_get_agenda_does_not_commit_or_rollback` | `backend/app/services/agenda.py` | `+    session.commit()` | `E   AssertionError: assert ['commit'] == []` |
| 30 | `test_get_agenda_appointment_returns_mapped_appointment_or_none` | `backend/app/services/agenda.py` | `-        status=appointment.status.value, +        status="reservado",` | `E   AssertionError: assert 'reservado' == 'cancelado'` |
| 31 | `test_agenda_for_one_day_returns_complete_envelope` | `backend/app/api/agenda.py` | `-        timezone=agenda.timezone, +        timezone="UTC",` | `E   AssertionError: assert 'UTC' == 'America/Arge.../Buenos_Aires'` |
| 32 | `test_agenda_for_a_week_returns_the_appointments_of_the_range` | `backend/app/api/agenda.py` | `-        to_date=agenda.to_date, +        to_date=agenda.from_date,` | `E   AssertionError: assert '2026-11-16' == '2026-11-22'` |
| 33 | `test_agenda_of_eight_days_crosses_two_weeks_in_order` | `backend/app/services/agenda.py` | `-        appointments=tuple(_to_agenda_appointment(row) for row in rows), +     ` | `E   AssertionError: assert ['7b9f4ae2-f1...3f76521f19c6'] == ['23faae40-57...a11` |
| 34 | `test_agenda_of_31_days_crosses_months` | `backend/app/api/schemas.py` | `-MAX_AGENDA_DAYS: Final = 31 +MAX_AGENDA_DAYS: Final = 30` | `E   AssertionError: {"errors":[{"field":null,"type":"invalid_range_length","mess` |
| 35 | `test_agenda_filter_by_professional_returns_their_appointments` | `backend/app/api/agenda.py` | `-        params.professional_id, +        None,` | `E   AssertionError: assert {'2212b168-8a...5b85775f9c02'} == {'457cff9c-e5...e19` |
| 36 | `test_agenda_filter_by_chair_returns_their_appointments` | `backend/app/api/agenda.py` | `-        params.chair_id, +        None,` | `E   AssertionError: assert {'19c9c0e1-1e...47ff73625c37'} == {'ae3b8768-16...47f` |
| 37 | `test_agenda_professional_and_chair_filters_combine` | `backend/app/repositories/appointment.py` | `-            stmt = stmt.where(AppointmentModel.professional_id == professional_` | `E   AssertionError: assert {'b9843149-c2...f59b76c7ec53'} == {'dbe84a3d-d2...97f` |
| 38 | `test_agenda_unknown_professional_returns_empty_lists` | `backend/app/repositories/appointment.py` | `-        if professional_id is not None: +        if False:` | `E   AssertionError: assert [{'chairId': ...99c779', ...}] == []` |
| 39 | `test_agenda_unknown_chair_empties_appointments_but_not_hours_or_blocks` | `backend/app/repositories/appointment.py` | `-        if chair_id is not None: +        if False:` | `E   AssertionError: assert [{'chairId': ...6d7a3a', ...}] == []` |
| 40 | `test_agenda_chair_filter_does_not_filter_hours_or_blocks` | `backend/app/services/agenda.py` | `-        if professional_id is None +        if professional_id is None and chai` | `E   AssertionError: assert {'end': '13:00', 'professionalId': '00000000-0000-000` |
| 41 | `test_agenda_dentist_sees_appointments_of_another_professional` | `backend/app/api/agenda.py` | `-        params.professional_id, +        params.professional_id or permission.a` | `E   AssertionError: []` |
| 42 | `test_agenda_working_hours_template_includes_all_professionals` | `backend/app/api/agenda.py` | `-            for slot in agenda.working_hours +            for slot in agenda.wo` | `E   AssertionError: assert {'end': '19:00', 'professionalId': '00000000-0000-000` |
| 43 | `test_agenda_professional_filter_also_filters_working_hours` | `backend/app/repositories/working_hours.py` | `-            .where(WorkingHoursModel.professional_id == professional_id) +     ` | `E   AssertionError: assert {'00000000-00...000000000001'} == {'00000000-00...000` |
| 44 | `test_agenda_block_inside_range_is_returned_with_reason` | `backend/app/api/agenda.py` | `-                reason=block.reason, +                reason=None,` | `E   AssertionError: assert [{'endAt': '2...': None, ...}] == [{'endAt': '2...ngr` |
| 45 | `test_agenda_block_starting_before_the_range_is_included` | `backend/app/repositories/blocks.py` | `-            BlockModel.end_at > start_at, +            BlockModel.start_at >= s` | `E   AssertionError: assert [] == ['Guardia']` |
| 46 | `test_agenda_professional_filter_also_filters_blocks` | `backend/app/services/agenda.py` | `-        window_start, window_end, professional_id=professional_id +        wind` | `E   AssertionError: assert ['292d0980-bc...a541a0d021ed'] == ['292d0980-bc...4a3` |
| 47 | `test_agenda_includes_cancelled_appointments_with_their_status` | `backend/app/repositories/appointment.py` | `-        status=AppointmentStatus(row.status), +        status=AppointmentStatus` | `E   AssertionError: assert 'reservado' == 'cancelado'` |
| 48 | `test_agenda_orders_appointments_blocks_and_working_hours` | `backend/app/services/agenda.py` | `-        blocks=blocks, +        blocks=tuple(reversed(blocks)),` | `E   AssertionError: assert ['9d05b91f-98...daae6471b240'] == ['37e7a7b0-92...93f` |
| 49 | `test_agenda_uses_one_query_per_resource_without_n_plus_one` | `backend/app/repositories/blocks.py` | `-        return tuple(self._to_domain(row) for row in self._session.scalars(stmt` | `E   AssertionError: assert 2 == 1` |
| 50 | `test_appointment_ending_at_midnight_appears_only_on_its_own_day` | `backend/app/repositories/appointment.py` | `-            AppointmentModel.start_at < end_at, +            AppointmentModel.s` | `E   AssertionError: [{'id': '78d81c8e-3d73-456a-b1df-a3d88d9cbde5', 'patientId':` |
| 51 | `test_appointment_starting_at_midnight_appears_only_on_its_own_day` | `backend/app/repositories/appointment.py` | `-            AppointmentModel.end_at > start_at, +            AppointmentModel.e` | `E   AssertionError: [{'id': 'bc90e099-92d4-4e22-bf09-b3f66a5a6656', 'patientId':` |
| 52 | `test_agenda_shows_the_replaced_hours_with_24_00_and_00_00` | `backend/app/api/agenda.py` | `-                end=f"{slot.end_minute // 60:02d}:{slot.end_minute % 60:02d}", ` | `E   AssertionError: assert [{'end': '00:...'weekday': 2}] == [{'end': '24:...'we` |
| 53 | `test_block_crossing_midnight_appears_on_both_days` | `backend/app/repositories/blocks.py` | `-            BlockModel.end_at > start_at, +            BlockModel.start_at >= s` | `E   AssertionError: assert [] == ['fe92008a-4e...98ea41578037']` |
| 54 | `test_missing_from_returns_400` | `backend/app/api/schemas.py` | `-        alias="from", description="Fecha local inicial en formato AAAA-MM-DD." ` | `E   AssertionError: assert [{'field': No...range_order'}] == [{'field': 'f...': ` |
| 55 | `test_missing_to_returns_400` | `backend/app/api/schemas.py` | `-        alias="to", +        default=date.min, alias="to",` | `E   AssertionError: assert [{'field': No...range_order'}] == [{'field': 't...': ` |
| 56 | `test_invalid_date_format_returns_400` | `backend/app/api/errors.py` | `-    "invalid_date_format": "La fecha debe tener formato AAAA-MM-DD.", +    "inv` | `E   AssertionError: assert [{'field': 'f...date_format'}] == [{'field': 'f...dat` |
| 57 | `test_to_before_from_returns_400` | `backend/app/api/errors.py` | `-    "invalid_range_order": "La fecha final no puede ser anterior a la inicial."` | `E   AssertionError: assert [{'field': No...range_order'}] == [{'field': No...ran` |
| 58 | `test_range_longer_than_31_days_returns_400` | `backend/app/api/schemas.py` | `-MAX_AGENDA_DAYS: Final = 31 +MAX_AGENDA_DAYS: Final = 32` | `E   AssertionError: {"from":"2026-11-16","to":"2026-12-17","timezone":"America/A` |
| 59 | `test_malformed_professional_id_returns_400` | `backend/app/api/schemas.py` | `-        alias="professionalId", +        alias="professional",` | `E   AssertionError: assert [{'field': 'p...a_forbidden'}] == [{'field': 'p...uid` |
| 60 | `test_malformed_chair_id_returns_400` | `backend/app/api/schemas.py` | `-        alias="chairId", +        alias="sillon",` | `E   AssertionError: assert [{'field': 'c...a_forbidden'}] == [{'field': 'c...uid` |
| 61 | `test_unknown_query_parameter_returns_400` | `backend/app/api/schemas.py` | `-    model_config = ConfigDict(populate_by_name=True, extra="forbid") +    model` | `E   AssertionError: {"from":"2026-11-16","to":"2026-11-16","timezone":"America/A` |
| 62 | `test_agenda_without_token_returns_401` | `backend/app/main.py` | `-protected_router.include_router(agenda_router) +pass` | `E   assert 404 == 401` |
| 63 | `test_detail_returns_the_enriched_appointment` | `backend/app/api/agenda.py` | `-        chair_name=item.chair_name, +        chair_name=item.service_name,` | `E   AssertionError: assert {'chairId': '...e2a7bc3', ...} == {'chairId': '...e2a` |
| 64 | `test_detail_shows_the_current_status_of_a_cancelled_appointment` | `backend/app/services/agenda.py` | `-        status=appointment.status.value, +        status="confirmado",` | `E   AssertionError: assert 'confirmado' == 'cancelado'` |
| 65 | `test_detail_of_unknown_appointment_returns_404` | `backend/app/api/appointments.py` | `-        raise NotFoundError("Turno no encontrado.") +        raise NotFoundErro` | `E   AssertionError: assert {'code': 'NOT...inexistente.'} == {'code': 'NOT... en` |
| 66 | `test_detail_with_malformed_uuid_returns_400` | `backend/app/api/appointments.py` | `-    "/{id}", +    "/{appointment_id}",` | `E   AssertionError: assert {'errors': [{...: 'missing'}]} == {'errors': [{...id_` |
| 67 | `test_detail_without_token_returns_401` | `backend/app/main.py` | `-protected_router.include_router(appointments_router) +pass` | `E   assert 404 == 401` |
| 68 | `test_dentist_reads_the_detail_of_another_professionals_appointment` | `backend/app/api/appointments.py` | `+    if permission.actor.professional_id not in (None, appointment.professional_` | `E   AssertionError: {"code":"NOT_FOUND","message":"Turno no encontrado."}` |
| 69 | `test_agenda_openapi_documents_parameters_responses_and_models` | `backend/app/api/agenda.py` | `-    responses={**permission_responses()}, +    responses={},` | `E   AssertionError: 403` |
| 70 | `test_appointment_detail_openapi_documents_responses_and_model` | `backend/app/api/appointments.py` | `-    responses={ -        **not_found_responses("Turno"), -        **permission_` | `E   AssertionError: 404` |
<!-- mutaciones:fin -->

## Trazabilidad

<!-- trazabilidad:inicio -->
| # | Spec | Requisito | Escenario | Test |
|---|---|---|---|---|
| 1 | agenda-api | Parámetros y validación de la agenda | Falta el parámetro from responde 400 | `tests/integration/test_api_agenda_validation.py::test_missing_from_returns_400` |
| 2 | agenda-api | Parámetros y validación de la agenda | Falta el parámetro to responde 400 | `tests/integration/test_api_agenda_validation.py::test_missing_to_returns_400` |
| 3 | agenda-api | Parámetros y validación de la agenda | Una fecha con formato inválido responde 400 | `tests/integration/test_api_agenda_validation.py::test_invalid_date_format_returns_400` |
| 4 | agenda-api | Parámetros y validación de la agenda | Un to anterior al from responde 400 | `tests/integration/test_api_agenda_validation.py::test_to_before_from_returns_400` |
| 5 | agenda-api | Parámetros y validación de la agenda | Un rango de más de 31 días responde 400 | `tests/integration/test_api_agenda_validation.py::test_range_longer_than_31_days_returns_400` |
| 6 | agenda-api | Parámetros y validación de la agenda | Un professionalId malformado responde 400 | `tests/integration/test_api_agenda_validation.py::test_malformed_professional_id_returns_400` |
| 7 | agenda-api | Parámetros y validación de la agenda | Un chairId malformado responde 400 | `tests/integration/test_api_agenda_validation.py::test_malformed_chair_id_returns_400` |
| 8 | agenda-api | Parámetros y validación de la agenda | Un parámetro de query desconocido responde 400 | `tests/integration/test_api_agenda_validation.py::test_unknown_query_parameter_returns_400` |
| 9 | agenda-api | Parámetros y validación de la agenda | La agenda sin token responde 401 | `tests/integration/test_api_agenda_validation.py::test_agenda_without_token_returns_401` |
| 10 | agenda-api | Sobre de respuesta de la agenda | La agenda de un día devuelve el sobre completo | `tests/integration/test_api_agenda.py::test_agenda_for_one_day_returns_complete_envelope` |
| 11 | agenda-api | Sobre de respuesta de la agenda | La agenda de una semana devuelve los turnos del rango | `tests/integration/test_api_agenda.py::test_agenda_for_a_week_returns_the_appointments_of_the_range` |
| 12 | agenda-api | Sobre de respuesta de la agenda | Un rango de ocho días cruza dos semanas | `tests/integration/test_api_agenda.py::test_agenda_of_eight_days_crosses_two_weeks_in_order` |
| 13 | agenda-api | Sobre de respuesta de la agenda | Un rango de 31 días cruza meses | `tests/integration/test_api_agenda.py::test_agenda_of_31_days_crosses_months` |
| 14 | agenda-api | Filtros y visibilidad de la agenda | El filtro por profesional devuelve sus turnos | `tests/integration/test_api_agenda.py::test_agenda_filter_by_professional_returns_their_appointments` |
| 15 | agenda-api | Filtros y visibilidad de la agenda | El filtro por sillón devuelve sus turnos | `tests/integration/test_api_agenda.py::test_agenda_filter_by_chair_returns_their_appointments` |
| 16 | agenda-api | Filtros y visibilidad de la agenda | Los filtros de profesional y sillón se combinan | `tests/integration/test_api_agenda.py::test_agenda_professional_and_chair_filters_combine` |
| 17 | agenda-api | Filtros y visibilidad de la agenda | Un professionalId inexistente devuelve listas vacías | `tests/integration/test_api_agenda.py::test_agenda_unknown_professional_returns_empty_lists` |
| 18 | agenda-api | Filtros y visibilidad de la agenda | Un chairId inexistente deja vacíos los turnos pero no los horarios ni los bloqueos | `tests/integration/test_api_agenda.py::test_agenda_unknown_chair_empties_appointments_but_not_hours_or_blocks` |
| 19 | agenda-api | Filtros y visibilidad de la agenda | El chairId no filtra horarios ni bloqueos | `tests/integration/test_api_agenda.py::test_agenda_chair_filter_does_not_filter_hours_or_blocks` |
| 20 | agenda-api | Filtros y visibilidad de la agenda | El odontólogo ve los turnos de otro profesional | `tests/integration/test_api_agenda.py::test_agenda_dentist_sees_appointments_of_another_professional` |
| 21 | agenda-api | Horarios de atención del rango | La plantilla semanal incluye a todos los profesionales | `tests/integration/test_api_agenda.py::test_agenda_working_hours_template_includes_all_professionals` |
| 22 | agenda-api | Horarios de atención del rango | El filtro por profesional también filtra los horarios | `tests/integration/test_api_agenda.py::test_agenda_professional_filter_also_filters_working_hours` |
| 23 | agenda-api | Bloqueos del rango | Un bloqueo dentro del rango se devuelve con su motivo | `tests/integration/test_api_agenda.py::test_agenda_block_inside_range_is_returned_with_reason` |
| 24 | agenda-api | Bloqueos del rango | Un bloqueo que empieza antes del rango se incluye | `tests/integration/test_api_agenda.py::test_agenda_block_starting_before_the_range_is_included` |
| 25 | agenda-api | Bloqueos del rango | El filtro por profesional también filtra los bloqueos | `tests/integration/test_api_agenda.py::test_agenda_professional_filter_also_filters_blocks` |
| 26 | agenda-api | Bloqueos del rango | Un bloqueo que cruza la medianoche aparece en los dos días | `tests/integration/test_api_agenda_midnight.py::test_block_crossing_midnight_appears_on_both_days` |
| 27 | agenda-api | Estados y orden de la agenda | Los turnos cancelados se incluyen con su estado | `tests/integration/test_api_agenda.py::test_agenda_includes_cancelled_appointments_with_their_status` |
| 28 | agenda-api | Estados y orden de la agenda | Turnos, bloqueos y horarios salen en orden estable | `tests/integration/test_api_agenda.py::test_agenda_orders_appointments_blocks_and_working_hours` |
| 29 | agenda-api | Borde de medianoche de los turnos | Un turno que termina a las 00:00 solo aparece en su día | `tests/integration/test_api_agenda_midnight.py::test_appointment_ending_at_midnight_appears_only_on_its_own_day ; tests/integration/test_api_agenda_midnight.py::test_appointment_starting_at_midnight_appears_only_on_its_own_day` |
| 30 | appointments-api | Consulta de un turno por id | El detalle devuelve el turno enriquecido | `tests/integration/test_api_appointment_detail.py::test_detail_returns_the_enriched_appointment` |
| 31 | appointments-api | Consulta de un turno por id | Un turno inexistente responde 404 | `tests/integration/test_api_appointment_detail.py::test_detail_of_unknown_appointment_returns_404` |
| 32 | appointments-api | Consulta de un turno por id | Un id con UUID malformado responde 400 | `tests/integration/test_api_appointment_detail.py::test_detail_with_malformed_uuid_returns_400` |
| 33 | appointments-api | Consulta de un turno por id | El detalle sin token responde 401 | `tests/integration/test_api_appointment_detail.py::test_detail_without_token_returns_401` |
| 34 | appointments-api | Consulta de un turno por id | El odontólogo lee el detalle de un turno ajeno | `tests/integration/test_api_appointment_detail.py::test_dentist_reads_the_detail_of_another_professionals_appointment` |
<!-- trazabilidad:fin -->
