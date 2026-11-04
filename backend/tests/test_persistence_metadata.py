from typing import cast

from sqlalchemy import CheckConstraint, String, Table


def test_catalog_models_register_expected_tables_and_columns() -> None:
    from app.db.base import Base
    from app.db import models

    assert set(Base.metadata.tables) == {
        "professional",
        "chair",
        "service",
        "patient",
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
