"""Operaciones públicas de ciclo de vida: literales ficticios de la spec C-10."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.model import Actor, Appointment, AppointmentStatus as S, Role
from app.domain.violations import Ok, Rejected, Violation, ViolationCode as V

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
U1 = UUID("00000000-0000-0000-0000-0000000000a1")
U2 = UUID("00000000-0000-0000-0000-0000000000a2")
U3 = UUID("00000000-0000-0000-0000-0000000000a3")
T1 = UUID("00000000-0000-0000-0000-0000000000f1")
T2 = UUID("00000000-0000-0000-0000-0000000000f2")
PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
CHAIR = UUID("00000000-0000-0000-0000-0000000000b1")
SERVICE = UUID("00000000-0000-0000-0000-0000000000d1")
UTC = timezone.utc
TZ = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)
START = datetime(2026, 10, 20, 13, tzinfo=UTC)
END = datetime(2026, 10, 20, 13, 30, tzinfo=UTC)
NAME = "Dra. Laura Quiroga"
RECEPTION = Actor(U2, Role.RECEPCION)
ADMIN = Actor(U3, Role.ADMINISTRADOR)
DENTIST = Actor(U1, Role.ODONTOLOGO, P1)
PREFIX = "El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local)"


def appointment(status: S = S.RESERVED) -> Appointment:
    return Appointment(T1, PATIENT, P1, CHAIR, SERVICE, START, END, status)


def test_attended_before_start_exact_message() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.ATTENDED, RECEPTION, NOW, NAME, TZ)
    assert result == Rejected((Violation(V.STATUS_CHANGE_TOO_EARLY,
        'El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "atendido" antes del inicio (momento actual: 20/10/2026 09:00:00, hora local).'),))


def assert_copy(original: Appointment, result: Ok, target: S) -> None:
    assert result.appointment == Appointment(
        original.id, original.patient_id, original.professional_id, original.chair_id,
        original.service_id, original.start_at, original.end_at, target,
    )
    assert result.appointment is not original


def test_change_reserved_to_confirmed_returns_copy() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment()
    result = change_status(original, S.CONFIRMED, ADMIN, NOW, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.CONFIRMED)
    assert original == appointment()


def test_cancel_reserved_returns_agenda_copy() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment()
    result = cancel_appointment(original, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.CANCELLED)
    assert original == appointment()


def test_cancel_confirmed_admin_returns_copy() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment(S.CONFIRMED)
    result = cancel_appointment(original, ADMIN, START - timedelta(seconds=1), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.CANCELLED)
    assert original == appointment(S.CONFIRMED)


def test_cancel_attended_rejected_exact_message() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment(S.ATTENDED)
    result = cancel_appointment(original, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(
        V.INVALID_TRANSITION,
        'El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".',
    ),)
    assert original == appointment(S.ATTENDED)


def test_cancel_terminal_no_show_preserves_original() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment(S.NO_SHOW)
    result = cancel_appointment(original, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "' + S.NO_SHOW.value + '" al estado "cancelado".'),)
    assert original == appointment(S.NO_SHOW)


def test_cancel_terminal_cancelled_preserves_original() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment(S.CANCELLED)
    result = cancel_appointment(original, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Rejected)
    assert result.violations == (Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "' + S.CANCELLED.value + '" al estado "cancelado".'),)
    assert original == appointment(S.CANCELLED)


def test_cancel_reserved_after_13_15_allowed() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment(S.RESERVED)
    result = cancel_appointment(original, RECEPTION, datetime(2026, 10, 20, 13, 15, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.CANCELLED)
    assert original == appointment(S.RESERVED)


def test_cancel_confirmed_after_14_0_allowed() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    original = appointment(S.CONFIRMED)
    result = cancel_appointment(original, RECEPTION, datetime(2026, 10, 20, 14, 0, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.CANCELLED)
    assert original == appointment(S.CONFIRMED)


def test_change_reserved_to_attended_at_start() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment(S.RESERVED)
    result = change_status(original, S.ATTENDED, RECEPTION, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.ATTENDED)
    assert original == appointment(S.RESERVED)


def test_change_reserved_to_no_show_at_start() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment(S.RESERVED)
    result = change_status(original, S.NO_SHOW, RECEPTION, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.NO_SHOW)
    assert original == appointment(S.RESERVED)


def test_change_confirmed_to_attended_at_start() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment(S.CONFIRMED)
    result = change_status(original, S.ATTENDED, RECEPTION, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.ATTENDED)
    assert original == appointment(S.CONFIRMED)


def test_change_confirmed_to_no_show_at_start() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment(S.CONFIRMED)
    result = change_status(original, S.NO_SHOW, RECEPTION, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(original, result, S.NO_SHOW)
    assert original == appointment(S.CONFIRMED)


def test_change_cancelled_requires_cancel_operation() -> None:
    from app.domain.appointment.transitions import change_status

    with pytest.raises(ValueError, match="cancel_appointment"):
        change_status(appointment(), S.CANCELLED, RECEPTION, NOW, NAME, TZ)


def test_change_cancelled_contract_precedes_foreign_permission() -> None:
    from app.domain.appointment.transitions import change_status

    with pytest.raises(ValueError, match="cancel_appointment"):
        change_status(appointment(), S.CANCELLED, Actor(U1, Role.ODONTOLOGO, P2), NOW, NAME, TZ)


def test_change_confirmed_to_reserved_rejected() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment(S.CONFIRMED)
    result = change_status(original, S.RESERVED, RECEPTION, NOW, NAME, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "confirmado" al estado "reservado".'),))
    assert original == appointment(S.CONFIRMED)


def test_change_reserved_diagonal_rejected() -> None:
    from app.domain.appointment.transitions import change_status

    original = appointment()
    assert change_status(original, S.RESERVED, RECEPTION, NOW, NAME, TZ) == Rejected((Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "reservado" al estado "reservado".'),))
    assert original == appointment()


def test_cancel_naive_now_raises() -> None:
    from app.domain.appointment.transitions import cancel_appointment

    with pytest.raises(ValueError, match="now.*zona"):
        cancel_appointment(appointment(), RECEPTION, datetime(2026, 10, 20, 9), NAME, TZ)


def test_change_naive_now_raises() -> None:
    from app.domain.appointment.transitions import change_status

    with pytest.raises(ValueError, match="now.*zona"):
        change_status(appointment(), S.CONFIRMED, RECEPTION, datetime(2026, 10, 20, 9), NAME, TZ)


def test_change_equivalent_zone_10() -> None:
    from app.domain.appointment.transitions import change_status

    now = datetime(2026, 10, 20, 10, tzinfo=timezone(timedelta(hours=-3)))
    result = change_status(appointment(S.CONFIRMED), S.ATTENDED, RECEPTION, now, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(S.CONFIRMED), result, S.ATTENDED)


def test_change_equivalent_zone_14() -> None:
    from app.domain.appointment.transitions import change_status

    now = datetime(2026, 10, 20, 14, tzinfo=timezone(timedelta(hours=1)))
    result = change_status(appointment(S.CONFIRMED), S.ATTENDED, RECEPTION, now, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(S.CONFIRMED), result, S.ATTENDED)


def test_dentist_foreign_change_forbidden_exact() -> None:
    from app.domain.appointment import change_status

    original = replace(appointment(), id=T2, professional_id=P2)
    result = change_status(original, S.CONFIRMED, DENTIST, START, NAME, TZ)
    assert result == Rejected((Violation(V.FORBIDDEN_OPERATION,
        'No tiene permiso para cambiar el estado del turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): un odontólogo solo puede cambiar el estado de sus propios turnos.'),))
    assert original == replace(appointment(), id=T2, professional_id=P2)


def test_dentist_own_confirmed_uses_professional_not_user() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.RESERVED), S.CONFIRMED, DENTIST, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(S.RESERVED), result, S.CONFIRMED)
    assert U1 != P1


def test_dentist_own_attended_uses_professional_not_user() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.RESERVED), S.ATTENDED, DENTIST, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(S.RESERVED), result, S.ATTENDED)
    assert U1 != P1


def test_dentist_own_no_show_uses_professional_not_user() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.CONFIRMED), S.NO_SHOW, DENTIST, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(S.CONFIRMED), result, S.NO_SHOW)
    assert U1 != P1


def test_dentist_foreign_attended_forbidden() -> None:
    from app.domain.appointment import change_status

    original = replace(appointment(), id=T2, professional_id=P2)
    result = change_status(original, S.ATTENDED, DENTIST, START, NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.FORBIDDEN_OPERATION]
    assert original == replace(appointment(), id=T2, professional_id=P2)


def test_dentist_cannot_cancel_own_exact_message() -> None:
    from app.domain.appointment import cancel_appointment

    original = appointment()
    result = cancel_appointment(original, DENTIST, NOW, NAME, TZ)
    assert result == Rejected((Violation(V.FORBIDDEN_OPERATION,
        'No tiene permiso para cancelar el turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): solo recepción y administración pueden cancelar turnos.'),))
    assert original == appointment()


def test_dentist_cannot_cancel_foreign_confirmed() -> None:
    from app.domain.appointment import cancel_appointment

    original = replace(appointment(S.CONFIRMED), id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    result = cancel_appointment(original, DENTIST, NOW, "Dra. Inés Molina", TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.FORBIDDEN_OPERATION]
    assert original.status is S.CONFIRMED


def test_management_recepcion_t1_confirm() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    actor = Actor(U2, Role.RECEPCION)
    result = change_status(original, S.CONFIRMED, actor, NOW, NAME, TZ)
    target = S.CONFIRMED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_recepcion_t1_cancel() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    actor = Actor(U2, Role.RECEPCION)
    result = cancel_appointment(original, actor, NOW, NAME, TZ)
    target = S.CANCELLED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_recepcion_t2_confirm() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    original = replace(original, id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    actor = Actor(U2, Role.RECEPCION)
    result = change_status(original, S.CONFIRMED, actor, NOW, NAME, TZ)
    target = S.CONFIRMED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_recepcion_t2_cancel() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    original = replace(original, id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    actor = Actor(U2, Role.RECEPCION)
    result = cancel_appointment(original, actor, NOW, NAME, TZ)
    target = S.CANCELLED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_administrador_t1_confirm() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    actor = Actor(U3, Role.ADMINISTRADOR)
    result = change_status(original, S.CONFIRMED, actor, NOW, NAME, TZ)
    target = S.CONFIRMED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_administrador_t1_cancel() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    actor = Actor(U3, Role.ADMINISTRADOR)
    result = cancel_appointment(original, actor, NOW, NAME, TZ)
    target = S.CANCELLED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_administrador_t2_confirm() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    original = replace(original, id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    actor = Actor(U3, Role.ADMINISTRADOR)
    result = change_status(original, S.CONFIRMED, actor, NOW, NAME, TZ)
    target = S.CONFIRMED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_management_administrador_t2_cancel() -> None:
    from app.domain.appointment import cancel_appointment, change_status

    original = appointment()
    original = replace(original, id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    actor = Actor(U3, Role.ADMINISTRADOR)
    result = cancel_appointment(original, actor, NOW, NAME, TZ)
    target = S.CANCELLED
    assert isinstance(result, Ok)
    assert_copy(original, result, target)
    assert original.status is S.RESERVED


def test_no_show_before_start_exact_message() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.CONFIRMED), S.NO_SHOW, RECEPTION, NOW, NAME, TZ)
    assert result == Rejected((Violation(V.STATUS_CHANGE_TOO_EARLY,
        'El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "ausente" antes del inicio (momento actual: 20/10/2026 09:00:00, hora local).'),))


def test_time_attended_equal() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.ATTENDED, RECEPTION, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.ATTENDED)


def test_time_attended_micro_before() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.ATTENDED, RECEPTION, datetime(2026, 10, 20, 12, 59, 59, 999999, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.STATUS_CHANGE_TOO_EARLY]


def test_time_attended_micro_after() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.ATTENDED, RECEPTION, datetime(2026, 10, 20, 13, 0, 0, 1, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.ATTENDED)


def test_time_attended_during() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.ATTENDED, RECEPTION, datetime(2026, 10, 20, 13, 15, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.ATTENDED)


def test_time_attended_seconds_before() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.ATTENDED, RECEPTION, datetime(2026, 10, 20, 12, 59, 30, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.STATUS_CHANGE_TOO_EARLY]


def test_time_no_show_equal() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.NO_SHOW, RECEPTION, START, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.NO_SHOW)


def test_time_no_show_micro_before() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.NO_SHOW, RECEPTION, datetime(2026, 10, 20, 12, 59, 59, 999999, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.STATUS_CHANGE_TOO_EARLY]


def test_time_no_show_micro_after() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.NO_SHOW, RECEPTION, datetime(2026, 10, 20, 13, 0, 0, 1, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.NO_SHOW)


def test_time_no_show_during() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.NO_SHOW, RECEPTION, datetime(2026, 10, 20, 13, 15, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.NO_SHOW)


def test_time_no_show_seconds_before() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.NO_SHOW, RECEPTION, datetime(2026, 10, 20, 12, 59, 30, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.STATUS_CHANGE_TOO_EARLY]


def test_confirmation_time_before() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.CONFIRMED, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.CONFIRMED)


def test_confirmation_time_after() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.CONFIRMED, RECEPTION, datetime(2026, 10, 20, 14, tzinfo=UTC), NAME, TZ)
    assert isinstance(result, Ok)
    assert_copy(appointment(), result, S.CONFIRMED)


def test_authorized_invalid_transition_and_early_attended_order() -> None:
    from app.domain.appointment import change_status

    original = appointment(S.CANCELLED)
    result = change_status(original, S.ATTENDED, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.INVALID_TRANSITION, V.STATUS_CHANGE_TOO_EARLY]
    assert original == appointment(S.CANCELLED)


def test_authorized_invalid_transition_and_early_no_show_order() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.CANCELLED), S.NO_SHOW, RECEPTION, NOW, NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.INVALID_TRANSITION, V.STATUS_CHANGE_TOO_EARLY]


def test_invalid_transition_time_fulfilled_no_show() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.ATTENDED), S.NO_SHOW, RECEPTION, END, NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.INVALID_TRANSITION]


def test_invalid_transition_time_fulfilled_confirmed() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(S.ATTENDED), S.CONFIRMED, RECEPTION, END, NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.INVALID_TRANSITION]


def test_permission_hides_invalid_and_early_attended() -> None:
    from app.domain.appointment import change_status

    original = replace(appointment(S.CANCELLED), id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    result = change_status(original, S.ATTENDED, DENTIST, NOW, "Dra. Inés Molina", TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.FORBIDDEN_OPERATION]
    assert original.status is S.CANCELLED


def test_permission_hides_invalid_and_early_no_show() -> None:
    from app.domain.appointment import change_status

    original = replace(appointment(S.CANCELLED), id=T2, professional_id=P2, start_at=START + timedelta(hours=1), end_at=END + timedelta(hours=1))
    result = change_status(original, S.NO_SHOW, DENTIST, NOW, "Dra. Inés Molina", TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.FORBIDDEN_OPERATION]
    assert original.status is S.CANCELLED


def test_own_terminal_cancel_permission_only() -> None:
    from app.domain.appointment import cancel_appointment

    original = appointment(S.ATTENDED)
    result = cancel_appointment(original, DENTIST, NOW, NAME, TZ)
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.FORBIDDEN_OPERATION]
    assert original == appointment(S.ATTENDED)


def test_transition_name_trim_exact() -> None:
    from app.domain.appointment import cancel_appointment

    name = '  Dra. Laura Quiroga  '
    result = cancel_appointment(appointment(S.ATTENDED), RECEPTION, NOW, name, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, 'El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".'),))
    assert name == '  Dra. Laura Quiroga  '


def test_transition_name_empty_exact() -> None:
    from app.domain.appointment import cancel_appointment

    name = ''
    result = cancel_appointment(appointment(S.ATTENDED), RECEPTION, NOW, name, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, 'El turno de el profesional del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".'),))
    assert name == ''


def test_transition_name_blank_exact() -> None:
    from app.domain.appointment import cancel_appointment

    name = '   '
    result = cancel_appointment(appointment(S.ATTENDED), RECEPTION, NOW, name, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, 'El turno de el profesional del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".'),))
    assert name == '   '


def test_transition_name_internal_exact() -> None:
    from app.domain.appointment import cancel_appointment

    name = 'Dra. Laura  Quiroga'
    result = cancel_appointment(appointment(S.ATTENDED), RECEPTION, NOW, name, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, 'El turno de Dra. Laura  Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".'),))
    assert name == 'Dra. Laura  Quiroga'


def test_foreign_dentist_for_t1_exact_message() -> None:
    from app.domain.appointment import change_status

    result = change_status(appointment(), S.CONFIRMED, Actor(U1, Role.ODONTOLOGO, P2), NOW, NAME, TZ)
    assert result == Rejected((Violation(V.FORBIDDEN_OPERATION,
        'No tiene permiso para cambiar el estado del turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local): un odontólogo solo puede cambiar el estado de sus propios turnos.'),))


def test_invalid_transition_uses_local_day_not_utc() -> None:
    from app.domain.appointment import cancel_appointment

    original = replace(appointment(S.ATTENDED), start_at=datetime(2026, 10, 21, 1, tzinfo=UTC), end_at=datetime(2026, 10, 21, 1, 30, tzinfo=UTC))
    result = cancel_appointment(original, RECEPTION, NOW, NAME, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION,
        'El turno de Dra. Laura Quiroga del 20/10/2026 de 22:00 a 22:30 (hora local) no puede pasar del estado "atendido" al estado "cancelado".'),))


def test_early_message_now_retains_seconds() -> None:
    from app.domain.appointment import change_status

    now = datetime(2026, 10, 20, 12, 59, 30, tzinfo=UTC)
    result = change_status(appointment(), S.ATTENDED, RECEPTION, now, NAME, TZ)
    assert result == Rejected((Violation(V.STATUS_CHANGE_TOO_EARLY,
        'El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00 a 10:30 (hora local) todavía no empezó: no se puede marcar como "atendido" antes del inicio (momento actual: 20/10/2026 09:59:30, hora local).'),))


@pytest.mark.parametrize("kind", ["transition", "early", "foreign", "cancel"])
def test_violation_metadata_never_claims_conflict(kind: str) -> None:
    from app.domain.appointment import cancel_appointment, change_status

    if kind == "transition":
        result = cancel_appointment(appointment(S.ATTENDED), RECEPTION, NOW, NAME, TZ)
        expected = V.INVALID_TRANSITION
    elif kind == "early":
        result = change_status(appointment(), S.ATTENDED, RECEPTION, NOW, NAME, TZ)
        expected = V.STATUS_CHANGE_TOO_EARLY
    elif kind == "foreign":
        result = change_status(appointment(), S.CONFIRMED, Actor(U1, Role.ODONTOLOGO, P2), NOW, NAME, TZ)
        expected = V.FORBIDDEN_OPERATION
    else:
        result = cancel_appointment(appointment(), DENTIST, NOW, NAME, TZ)
        expected = V.FORBIDDEN_OPERATION
    assert isinstance(result, Rejected)
    assert len(result.violations) == 1
    violation = result.violations[0]
    assert violation.code is expected
    assert violation.reference_kind is None
    assert violation.conflicting_appointment_id is None
    assert violation.conflicting_block_id is None
    assert violation.conflicting_interval is None


def test_interval_message_retains_seconds_and_fractional_time_shape() -> None:
    from app.domain.appointment import cancel_appointment

    original = replace(appointment(S.ATTENDED), start_at=datetime(2026, 10, 20, 13, 0, 5, tzinfo=UTC), end_at=datetime(2026, 10, 20, 13, 30, 0, 1, tzinfo=UTC))
    result = cancel_appointment(original, RECEPTION, NOW, NAME, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION,
        'El turno de Dra. Laura Quiroga del 20/10/2026 de 10:00:05 a 10:30:00 (hora local) no puede pasar del estado "atendido" al estado "cancelado".'),))


def test_diagonal_confirmed_invalid() -> None:
    from app.domain.appointment import change_status

    original = appointment(S.CONFIRMED)
    result = change_status(original, S.CONFIRMED, RECEPTION, END, NAME, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "' + S.CONFIRMED.value + '" al estado "' + S.CONFIRMED.value + '".'),))
    assert original == appointment(S.CONFIRMED)


def test_diagonal_attended_invalid() -> None:
    from app.domain.appointment import change_status

    original = appointment(S.ATTENDED)
    result = change_status(original, S.ATTENDED, RECEPTION, END, NAME, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "' + S.ATTENDED.value + '" al estado "' + S.ATTENDED.value + '".'),))
    assert original == appointment(S.ATTENDED)


def test_diagonal_no_show_invalid() -> None:
    from app.domain.appointment import change_status

    original = appointment(S.NO_SHOW)
    result = change_status(original, S.NO_SHOW, RECEPTION, END, NAME, TZ)
    assert result == Rejected((Violation(V.INVALID_TRANSITION, PREFIX + ' no puede pasar del estado "' + S.NO_SHOW.value + '" al estado "' + S.NO_SHOW.value + '".'),))
    assert original == appointment(S.NO_SHOW)
