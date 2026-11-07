from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from tests.integration.agenda_api_support import (
    P1_ID,
    add_block,
    agenda_data,
    book,
    future_monday,
    get_agenda,
    items,
    local_at,
    only,
    token_for,
    utc_z,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("agenda_data")]

__all__ = ["agenda_data"]


def replace_p1_hours_around_midnight(client: TestClient) -> None:
    """C2: el horario demo termina a las 19:00, así que se reemplaza por PUT (C-21)."""
    headers = token_for(client, "administrador")
    res = client.put(
        f"/api/professionals/{P1_ID}/working-hours",
        json=[
            {"weekday": 1, "start": "23:00", "end": "24:00"},
            {"weekday": 2, "start": "00:00", "end": "01:00"},
        ],
        headers=headers,
    )
    assert res.status_code == 200, res.text


def book_midnight_pair(client: TestClient) -> tuple[str, str]:
    replace_p1_hours_around_midnight(client)
    headers = token_for(client, "recepcion")
    monday = future_monday()
    tuesday = monday + timedelta(days=1)
    late = book(client, headers, local_at(monday, 23, 30))
    early = book(client, headers, local_at(tuesday, 0))
    return late, early


def test_appointment_ending_at_midnight_appears_only_on_its_own_day(
    auth_client: TestClient,
) -> None:
    late, early = book_midnight_pair(auth_client)
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()

    body = get_agenda(auth_client, headers, monday, monday)

    entry = only(items(body, "appointments"))
    assert entry["id"] == late
    assert entry["startAt"] == utc_z(local_at(monday, 23, 30))
    assert entry["endAt"] == utc_z(local_at(monday + timedelta(days=1), 0))
    assert early not in [item["id"] for item in items(body, "appointments")]


def test_appointment_starting_at_midnight_appears_only_on_its_own_day(
    auth_client: TestClient,
) -> None:
    late, early = book_midnight_pair(auth_client)
    headers = token_for(auth_client, "recepcion")
    tuesday = future_monday() + timedelta(days=1)

    body = get_agenda(auth_client, headers, tuesday, tuesday)

    entry = only(items(body, "appointments"))
    assert entry["id"] == early
    assert entry["startAt"] == utc_z(local_at(tuesday, 0))
    assert late not in [item["id"] for item in items(body, "appointments")]


def test_agenda_shows_the_replaced_hours_with_24_00_and_00_00(auth_client: TestClient) -> None:
    replace_p1_hours_around_midnight(auth_client)
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()

    body = get_agenda(auth_client, headers, monday, monday + timedelta(days=1))

    p1_hours = [h for h in items(body, "workingHours") if h["professionalId"] == str(P1_ID)]
    assert p1_hours == [
        {"professionalId": str(P1_ID), "weekday": 1, "start": "23:00", "end": "24:00"},
        {"professionalId": str(P1_ID), "weekday": 2, "start": "00:00", "end": "01:00"},
    ]


def test_block_crossing_midnight_appears_on_both_days(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    tuesday = monday + timedelta(days=1)
    block_id = add_block(
        auth_client, P1_ID, local_at(monday, 23), local_at(tuesday, 1), "Guardia"
    )

    monday_body = get_agenda(auth_client, headers, monday, monday)
    tuesday_body = get_agenda(auth_client, headers, tuesday, tuesday)

    assert [b["id"] for b in items(monday_body, "blocks")] == [block_id]
    assert [b["id"] for b in items(tuesday_body, "blocks")] == [block_id]
    assert items(monday_body, "blocks")[0]["reason"] == "Guardia"
