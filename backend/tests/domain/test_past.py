from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.domain.rules.past import check_not_in_the_past
from app.domain.violations import ViolationCode

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")

# Martes 2026-10-20, 10:00 hora local = 13:00 UTC.
NOW = datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc)


def test_check_not_in_the_past_start_five_minutes_before_now_reports_in_the_past() -> None:
    # 09:55 hora local = 12:55 UTC
    start = datetime(2026, 10, 20, 12, 55, tzinfo=timezone.utc)

    violations = check_not_in_the_past(start, NOW, BUENOS_AIRES)

    assert [v.code for v in violations] == [ViolationCode.IN_THE_PAST]
    assert violations[0].conflicting_appointment_id is None
    assert violations[0].conflicting_block_id is None
    assert violations[0].reference_kind is None


def test_check_not_in_the_past_start_equal_to_now_reports_nothing() -> None:
    # 10:00 hora local = 13:00 UTC
    start = datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc)

    assert check_not_in_the_past(start, NOW, BUENOS_AIRES) == []


@pytest.mark.parametrize(
    ("now", "start", "expected_codes"),
    [
        # inicio 10:05 hora local (13:05 UTC), now 10:00 -> valido
        (
            datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 13, 5, tzinfo=timezone.utc),
            [],
        ),
        # now 10:00:30 (13:00:30 UTC), inicio 10:00 (13:00 UTC) -> pasado
        (
            datetime(2026, 10, 20, 13, 0, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            [ViolationCode.IN_THE_PAST],
        ),
        # now 10:00:30, inicio 10:05 (13:05 UTC) -> valido
        (
            datetime(2026, 10, 20, 13, 0, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 13, 5, tzinfo=timezone.utc),
            [],
        ),
        # now 13:00:00.000001 UTC, inicio 10:00 (13:00 UTC) -> pasado
        (
            datetime(2026, 10, 20, 13, 0, 0, 1, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            [ViolationCode.IN_THE_PAST],
        ),
    ],
    ids=["inicio-posterior", "segundos-mismo-minuto", "segundos-paso-siguiente", "microsegundo"],
)
def test_check_not_in_the_past_compares_instants_strictly_without_truncating(
    now: datetime, start: datetime, expected_codes: list[ViolationCode]
) -> None:
    violations = check_not_in_the_past(start, now, BUENOS_AIRES)

    assert [v.code for v in violations] == expected_codes


@pytest.mark.parametrize(
    ("now", "start", "expected_message"),
    [
        # Mensaje de un turno en el pasado: now 10:00:00, inicio 09:55 (12:55 UTC)
        (
            datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 12, 55, tzinfo=timezone.utc),
            "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento "
            "actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado.",
        ),
        # Mismo minuto: now 10:00:30, inicio 10:00
        (
            datetime(2026, 10, 20, 13, 0, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento "
            "actual (20/10/2026 10:00:30, hora local): no se pueden dar turnos en el pasado.",
        ),
        # Fecha local y no la de UTC: now 02:30 UTC del 21 = 23:30 local del 20
        (
            datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 21, 2, 0, tzinfo=timezone.utc),
            "El inicio del turno (20/10/2026 23:00, hora local) es anterior al momento "
            "actual (20/10/2026 23:30:00, hora local): no se pueden dar turnos en el pasado.",
        ),
    ],
    ids=["cinco-minutos-antes", "mismo-minuto", "fecha-local-no-utc"],
)
def test_check_not_in_the_past_message_uses_local_date_and_now_with_seconds(
    now: datetime, start: datetime, expected_message: str
) -> None:
    violations = check_not_in_the_past(start, now, BUENOS_AIRES)

    assert [v.message for v in violations] == [expected_message]
