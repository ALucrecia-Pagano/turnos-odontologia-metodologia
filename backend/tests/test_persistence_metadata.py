from typing import cast

from sqlalchemy import CheckConstraint, DateTime, String, Table


def test_catalog_models_register_expected_tables_and_columns() -> None:
    from app.db.base import Base
    from app.db import models

    assert set(Base.metadata.tables) == {
        "professional",
        "chair",
        "service",
        "patient",
        "working_hours",
        "block",
    }
    assert models.ProfessionalModel.__table__.c.id.type.__class__.__name__ == "Uuid"
    patient_table = cast(Table, models.PatientModel.__table__)
    assert isinstance(patient_table.c.dni.type, String)
    assert patient_table.c.dni.type.length == 8
    assert models.ProfessionalModel.__table__.c.license_number.nullable is True
    assert models.ProfessionalModel.__table__.c.active.default.arg is True
    assert any(
        index.unique and index.columns.keys() == ["name_normalized"]
        for index in cast(Table, models.ChairModel.__table__).indexes
    )
    assert any(
        index.unique and index.columns.keys() == ["name_normalized"]
        for index in cast(Table, models.ServiceModel.__table__).indexes
    )
    assert any(
        index.unique and index.columns.keys() == ["dni"]
        for index in patient_table.indexes
    )


def test_catalog_constraints_are_explicit_and_stable() -> None:
    from app.db import models

    patient_table = cast(Table, models.PatientModel.__table__)
    patient_constraints = patient_table.constraints
    check = next(c for c in patient_constraints if isinstance(c, CheckConstraint))
    assert check.name == "ck_patient_dni_format"
    assert any(index.name == "ux_patient_dni" for index in patient_table.indexes)


def test_availability_models_register_expected_columns_constraints_and_indexes() -> None:
    from app.db import models

    working = cast(Table, models.WorkingHoursModel.__table__)
    block = cast(Table, models.BlockModel.__table__)
    assert working.c.id.type.__class__.__name__ == "Uuid"
    assert working.c.professional_id.type.__class__.__name__ == "Uuid"
    assert working.c.weekday.type.__class__.__name__ == "Integer"
    assert working.c.start_minute.type.__class__.__name__ == "Integer"
    assert working.c.end_minute.type.__class__.__name__ == "Integer"
    assert block.c.start_at.type.__class__.__name__ == "DateTime"
    assert cast(DateTime, block.c.start_at.type).timezone is True
    assert isinstance(block.c.reason.type, String)
    assert block.c.reason.type.length == 255
    assert {
        constraint.name for constraint in working.constraints
    } >= {
        "fk_working_hours_professional_id_professional",
        "ck_working_hours_weekday_range",
        "ck_working_hours_minute_range",
        "uq_working_hours_professional_weekday_start",
    }
    assert {
        constraint.name for constraint in block.constraints
    } >= {"fk_block_professional_id_professional", "ck_block_interval_order"}
    assert {
        index.name for index in working.indexes
    } >= {"ix_working_hours_professional_id_weekday"}
    assert {
        index.name for index in block.indexes
    } >= {"ix_block_professional_id_start_at_end_at"}
