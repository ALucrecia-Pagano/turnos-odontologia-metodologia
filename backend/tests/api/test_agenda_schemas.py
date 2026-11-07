from datetime import date, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.api.schemas import AgendaQuery

PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAIR_ID = UUID("00000000-0000-0000-0000-0000000000b1")


def day(offset: int = 0) -> date:
    """Fecha local relativa a hoy (los tests no dependen de fechas fijas)."""
    return date.today() + timedelta(days=30 + offset)


def error_types(exc: ValidationError) -> list[tuple[str, str]]:
    return [(".".join(str(part) for part in err["loc"]), err["type"]) for err in exc.errors()]


def test_agenda_query_parses_dates_and_aliases() -> None:
    query = AgendaQuery.model_validate(
        {"from": day().isoformat(), "to": day(6).isoformat()}
    )
    assert query.from_date == day()
    assert query.to_date == day(6)
    assert query.professional_id is None
    assert query.chair_id is None


def test_agenda_query_accepts_single_day_and_31_day_ranges() -> None:
    one_day = AgendaQuery.model_validate({"from": day().isoformat(), "to": day().isoformat()})
    assert one_day.from_date == one_day.to_date
    full = AgendaQuery.model_validate({"from": day().isoformat(), "to": day(30).isoformat()})
    assert (full.to_date - full.from_date).days + 1 == 31


def test_agenda_query_rejects_range_longer_than_31_days() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AgendaQuery.model_validate({"from": day().isoformat(), "to": day(31).isoformat()})
    assert error_types(excinfo.value) == [("", "invalid_range_length")]
    assert excinfo.value.errors()[0]["msg"] == "El rango no puede superar los 31 días."


def test_agenda_query_rejects_to_before_from() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AgendaQuery.model_validate({"from": day(1).isoformat(), "to": day().isoformat()})
    assert error_types(excinfo.value) == [("", "invalid_range_order")]
    assert (
        excinfo.value.errors()[0]["msg"]
        == "La fecha final no puede ser anterior a la inicial."
    )


def test_agenda_query_rejects_invalid_date_format() -> None:
    valid = day().isoformat()
    for bad in ("09-11-2026", f"{valid}T10:00:00-03:00", "2026-13-45", "2026-1-9"):
        with pytest.raises(ValidationError) as excinfo:
            AgendaQuery.model_validate({"from": bad, "to": valid})
        assert error_types(excinfo.value) == [("from", "invalid_date_format")], bad
        assert excinfo.value.errors()[0]["msg"] == "La fecha debe tener formato AAAA-MM-DD."
    with pytest.raises(ValidationError) as excinfo:
        AgendaQuery.model_validate({"from": valid, "to": "mañana"})
    assert error_types(excinfo.value) == [("to", "invalid_date_format")]


def test_agenda_query_requires_from_and_to() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AgendaQuery.model_validate({})
    assert sorted(error_types(excinfo.value)) == [("from", "missing"), ("to", "missing")]


def test_agenda_query_professional_and_chair_ids_are_optional_uuids() -> None:
    query = AgendaQuery.model_validate(
        {
            "from": day().isoformat(),
            "to": day().isoformat(),
            "professionalId": str(PROFESSIONAL_ID),
            "chairId": str(CHAIR_ID),
        }
    )
    assert query.professional_id == PROFESSIONAL_ID
    assert query.chair_id == CHAIR_ID
    with pytest.raises(ValidationError) as excinfo:
        AgendaQuery.model_validate(
            {
                "from": day().isoformat(),
                "to": day().isoformat(),
                "professionalId": "no-es-un-uuid",
                "chairId": "tampoco",
            }
        )
    assert sorted(error_types(excinfo.value)) == [
        ("chairId", "uuid_parsing"),
        ("professionalId", "uuid_parsing"),
    ]


def test_agenda_query_forbids_extra_parameters() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AgendaQuery.model_validate(
            {"from": day().isoformat(), "to": day().isoformat(), "status": "cancelado"}
        )
    assert error_types(excinfo.value) == [("status", "extra_forbidden")]


def test_agenda_query_model_dump_by_alias() -> None:
    query = AgendaQuery.model_validate(
        {
            "from": day().isoformat(),
            "to": day(1).isoformat(),
            "professionalId": str(PROFESSIONAL_ID),
        }
    )
    assert query.model_dump(by_alias=True) == {
        "from": day(),
        "to": day(1),
        "professionalId": PROFESSIONAL_ID,
        "chairId": None,
    }
