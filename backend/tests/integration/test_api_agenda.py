import re
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event

from tests.integration.agenda_api_support import (
    CHAIR_1_ID,
    CHAIR_2_ID,
    P1_ID,
    P2_ID,
    PATIENT_1_ID,
    PATIENT_2_ID,
    SERVICE_CONTROL_ID,
    UNKNOWN_ID,
    add_block,
    add_working_hours,
    agenda_data,
    book,
    cancel,
    future_monday,
    get_agenda,
    items,
    local_at,
    only,
    start_times,
    token_for,
    utc_z,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("agenda_data")]

# Reexportado para que pytest encuentre el fixture en este módulo.
__all__ = ["agenda_data"]


def book_four_filter_appointments(client: TestClient) -> dict[str, str]:
    """Cuatro turnos del lunes L: (P1, sillón 1), (P1, sillón 2), (P2, sillón 2), (P2, sillón 1)."""
    headers = token_for(client, "recepcion")
    monday = future_monday()
    ids = {
        "p1c1": book(client, headers, local_at(monday, 9), professional_id=P1_ID, chair_id=CHAIR_1_ID),
        "p1c2": book(client, headers, local_at(monday, 10), professional_id=P1_ID, chair_id=CHAIR_2_ID),
        "p2c2": book(client, headers, local_at(monday, 9), professional_id=P2_ID, chair_id=CHAIR_2_ID),
        "p2c1": book(client, headers, local_at(monday, 10), professional_id=P2_ID, chair_id=CHAIR_1_ID),
    }
    return ids


def appointment_ids(body: dict[str, object]) -> set[object]:
    return {entry["id"] for entry in items(body, "appointments")}


def test_agenda_for_one_day_returns_complete_envelope(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    start = local_at(monday, 10)
    appointment_id = book(auth_client, headers, start)

    body = get_agenda(auth_client, headers, monday, monday)

    assert body["from"] == monday.isoformat()
    assert body["to"] == monday.isoformat()
    assert body["timezone"] == "America/Argentina/Buenos_Aires"
    assert items(body, "appointments") == [
        {
            "id": appointment_id,
            "patientId": str(PATIENT_1_ID),
            "patientName": "Ana Pérez",
            "professionalId": str(P1_ID),
            "professionalName": "Dra. Laura Quiroga",
            "chairId": str(CHAIR_1_ID),
            "chairName": "Sillón 1",
            "serviceId": str(SERVICE_CONTROL_ID),
            "serviceName": "Control",
            "startAt": utc_z(start),
            "endAt": utc_z(start + timedelta(minutes=30)),
            "status": "reservado",
        }
    ]
    assert utc_z(start) == f"{monday.isoformat()}T13:00:00Z"
    assert {"professionalId": str(P1_ID), "weekday": 1, "start": "09:00", "end": "13:00"} in items(
        body, "workingHours"
    )
    assert items(body, "blocks") == []


def test_agenda_for_a_week_returns_the_appointments_of_the_range(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    appointment_id = book(auth_client, headers, local_at(monday, 10))

    body = get_agenda(auth_client, headers, monday, monday + timedelta(days=6))

    assert body["from"] == monday.isoformat()
    assert body["to"] == (monday + timedelta(days=6)).isoformat()
    assert [entry["id"] for entry in items(body, "appointments")] == [appointment_id]


def test_agenda_of_eight_days_crosses_two_weeks_in_order(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    monday = future_monday()
    next_monday = monday + timedelta(days=7)
    second = book(auth_client, headers, local_at(next_monday, 9))
    first = book(auth_client, headers, local_at(monday, 9))

    body = get_agenda(auth_client, headers, monday, next_monday)

    assert [entry["id"] for entry in items(body, "appointments")] == [first, second]
    assert start_times(body) == sorted(start_times(body), key=str)


def test_agenda_of_31_days_crosses_months(
    auth_client: TestClient, test_engine: Engine
) -> None:
    add_working_hours(test_engine, P1_ID, 3, 540, 780)
    headers = token_for(auth_client, "administrador")
    monday = future_monday()
    last_day = monday + timedelta(days=30)
    first = book(auth_client, headers, local_at(monday, 9))
    last = book(auth_client, headers, local_at(last_day, 9))

    body = get_agenda(auth_client, headers, monday, last_day)

    assert [entry["id"] for entry in items(body, "appointments")] == [first, last]
    beyond = get_agenda(auth_client, headers, monday, monday + timedelta(days=29))
    assert [entry["id"] for entry in items(beyond, "appointments")] == [first]


def test_agenda_filter_by_professional_returns_their_appointments(auth_client: TestClient) -> None:
    ids = book_four_filter_appointments(auth_client)
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()

    body = get_agenda(auth_client, headers, monday, monday, professionalId=str(P1_ID))

    assert appointment_ids(body) == {ids["p1c1"], ids["p1c2"]}
    assert {entry["professionalId"] for entry in items(body, "appointments")} == {str(P1_ID)}


def test_agenda_filter_by_chair_returns_their_appointments(auth_client: TestClient) -> None:
    ids = book_four_filter_appointments(auth_client)
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()

    body = get_agenda(auth_client, headers, monday, monday, chairId=str(CHAIR_1_ID))

    assert appointment_ids(body) == {ids["p1c1"], ids["p2c1"]}
    assert {entry["chairId"] for entry in items(body, "appointments")} == {str(CHAIR_1_ID)}


def test_agenda_professional_and_chair_filters_combine(auth_client: TestClient) -> None:
    ids = book_four_filter_appointments(auth_client)
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()

    body = get_agenda(
        auth_client, headers, monday, monday, professionalId=str(P1_ID), chairId=str(CHAIR_2_ID)
    )

    assert appointment_ids(body) == {ids["p1c2"]}


def test_agenda_unknown_professional_returns_empty_lists(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    book(auth_client, headers, local_at(monday, 10))
    add_block(auth_client, P1_ID, local_at(monday, 14), local_at(monday, 15), "Curso")

    body = get_agenda(auth_client, headers, monday, monday, professionalId=str(UNKNOWN_ID))

    assert items(body, "appointments") == []
    assert items(body, "workingHours") == []
    assert items(body, "blocks") == []


def test_agenda_unknown_chair_empties_appointments_but_not_hours_or_blocks(
    auth_client: TestClient,
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    book(auth_client, headers, local_at(monday, 10))
    add_block(auth_client, P1_ID, local_at(monday, 14), local_at(monday, 15), "Curso")

    body = get_agenda(auth_client, headers, monday, monday, chairId=str(UNKNOWN_ID))

    assert items(body, "appointments") == []
    assert items(body, "workingHours") != []
    assert items(body, "blocks") != []


def test_agenda_chair_filter_does_not_filter_hours_or_blocks(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    block_id = add_block(auth_client, P2_ID, local_at(monday, 14), local_at(monday, 15), "Curso")

    body = get_agenda(auth_client, headers, monday, monday, chairId=str(CHAIR_1_ID))

    hours = items(body, "workingHours")
    assert {"professionalId": str(P1_ID), "weekday": 1, "start": "09:00", "end": "13:00"} in hours
    assert {"professionalId": str(P2_ID), "weekday": 1, "start": "09:00", "end": "13:00"} in hours
    assert [entry["id"] for entry in items(body, "blocks")] == [block_id]


def test_agenda_dentist_sees_appointments_of_another_professional(auth_client: TestClient) -> None:
    reception = token_for(auth_client, "recepcion")
    monday = future_monday()
    appointment_id = book(
        auth_client,
        reception,
        local_at(monday, 9),
        professional_id=P2_ID,
        chair_id=CHAIR_2_ID,
        patient_id=PATIENT_2_ID,
    )
    dentist = token_for(auth_client, "odontologo")

    body = get_agenda(auth_client, dentist, monday, monday)

    entry = only(items(body, "appointments"))
    assert entry["id"] == appointment_id
    assert entry["professionalId"] == str(P2_ID)
    assert entry["professionalName"] == "Dr. Martín Sosa"


def test_agenda_working_hours_template_includes_all_professionals(
    auth_client: TestClient, test_engine: Engine
) -> None:
    add_working_hours(test_engine, P1_ID, 1, 900, 1140)
    headers = token_for(auth_client, "administrador")
    monday = future_monday()

    body = get_agenda(auth_client, headers, monday, monday)

    hours = items(body, "workingHours")
    assert {"professionalId": str(P1_ID), "weekday": 1, "start": "09:00", "end": "13:00"} in hours
    assert {"professionalId": str(P1_ID), "weekday": 1, "start": "15:00", "end": "19:00"} in hours
    assert {"professionalId": str(P2_ID), "weekday": 1, "start": "09:00", "end": "13:00"} in hours


def test_agenda_professional_filter_also_filters_working_hours(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    monday = future_monday()

    body = get_agenda(auth_client, headers, monday, monday, professionalId=str(P2_ID))

    hours = items(body, "workingHours")
    assert hours != []
    assert {entry["professionalId"] for entry in hours} == {str(P2_ID)}


def test_agenda_block_inside_range_is_returned_with_reason(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    block_id = add_block(auth_client, P2_ID, local_at(monday, 14), local_at(monday, 15), "Congreso")

    body = get_agenda(auth_client, headers, monday, monday)

    assert items(body, "blocks") == [
        {
            "id": block_id,
            "professionalId": str(P2_ID),
            "startAt": f"{monday.isoformat()}T17:00:00Z",
            "endAt": f"{monday.isoformat()}T18:00:00Z",
            "reason": "Congreso",
        }
    ]


def test_agenda_block_starting_before_the_range_is_included(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    monday = future_monday()
    sunday = monday - timedelta(days=1)
    add_block(auth_client, P1_ID, local_at(sunday, 23), local_at(monday, 1), "Guardia")

    body = get_agenda(auth_client, headers, monday, monday)

    assert [entry["reason"] for entry in items(body, "blocks")] == ["Guardia"]


def test_agenda_professional_filter_also_filters_blocks(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    monday = future_monday()
    mine = add_block(auth_client, P1_ID, local_at(monday, 14), local_at(monday, 15), "Propio")
    add_block(auth_client, P2_ID, local_at(monday, 16), local_at(monday, 17), "Ajeno")

    body = get_agenda(auth_client, headers, monday, monday, professionalId=str(P1_ID))

    assert [entry["id"] for entry in items(body, "blocks")] == [mine]


def test_agenda_includes_cancelled_appointments_with_their_status(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = future_monday()
    appointment_id = book(auth_client, headers, local_at(monday, 10))
    cancel(auth_client, headers, appointment_id)

    body = get_agenda(auth_client, headers, monday, monday)

    entry = only(items(body, "appointments"))
    assert entry["id"] == appointment_id
    assert entry["status"] == "cancelado"


def test_agenda_orders_appointments_blocks_and_working_hours(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    monday = future_monday()
    third = book(auth_client, headers, local_at(monday, 10), professional_id=P1_ID, chair_id=CHAIR_2_ID)
    first = book(auth_client, headers, local_at(monday, 9), professional_id=P1_ID, chair_id=CHAIR_1_ID)
    second = book(
        auth_client, headers, local_at(monday, 9, 30), professional_id=P2_ID, chair_id=CHAIR_2_ID
    )
    late_block = add_block(auth_client, P2_ID, local_at(monday, 11), local_at(monday, 11, 30), "B")
    early_block = add_block(auth_client, P1_ID, local_at(monday, 10, 30), local_at(monday, 11), "A")

    body = get_agenda(auth_client, headers, monday, monday)

    assert [entry["id"] for entry in items(body, "appointments")] == [first, second, third]
    assert [entry["id"] for entry in items(body, "blocks")] == [early_block, late_block]
    ordering = [
        (entry["professionalId"], entry["weekday"], entry["start"])
        for entry in items(body, "workingHours")
    ]
    assert ordering == sorted(ordering, key=lambda item: (str(item[0]), int(str(item[1])), str(item[2])))
    assert [entry["professionalId"] for entry in items(body, "workingHours")] == [
        str(P1_ID),
        str(P2_ID),
    ]


def test_agenda_uses_one_query_per_resource_without_n_plus_one(
    auth_client: TestClient, auth_app: FastAPI
) -> None:
    headers = token_for(auth_client, "administrador")
    monday = future_monday()
    for hour in (9, 10, 11, 12):
        book(auth_client, headers, local_at(monday, hour))
    add_block(auth_client, P1_ID, local_at(monday, 14), local_at(monday, 15), "Curso")
    statements: list[str] = []

    def count(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement)

    engine = auth_app.state.engine
    event.listen(engine, "before_cursor_execute", count)
    try:
        body = get_agenda(auth_client, headers, monday, monday)
    finally:
        event.remove(engine, "before_cursor_execute", count)

    assert len(items(body, "appointments")) == 4
    assert len([s for s in statements if re.search(r"FROM appointment\b", s)]) == 1
    assert len([s for s in statements if re.search(r"FROM block\b", s)]) == 1
    assert len([s for s in statements if re.search(r"FROM working_hours\b", s)]) == 1
    assert len([s for s in statements if re.search(r"FROM (patient|professional|chair|service)\b", s)]) == 0
