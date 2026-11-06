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
        "appointment",
        "appointment_status_change",
        "app_user",
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


def test_appointment_models_register_expected_columns_constraints_and_indexes() -> None:
    from app.db.base import Base
    from app.db import models

    assert {"appointment", "appointment_status_change"}.issubset(Base.metadata.tables)
    appointment = cast(Table, models.AppointmentModel.__table__)
    status_change = cast(Table, models.AppointmentStatusChangeModel.__table__)

    assert appointment.c.id.type.__class__.__name__ == "Uuid"
    assert appointment.c.patient_id.type.__class__.__name__ == "Uuid"
    assert appointment.c.professional_id.type.__class__.__name__ == "Uuid"
    assert appointment.c.chair_id.type.__class__.__name__ == "Uuid"
    assert appointment.c.service_id.type.__class__.__name__ == "Uuid"
    assert appointment.c.start_at.type.__class__.__name__ == "DateTime"
    assert cast(DateTime, appointment.c.start_at.type).timezone is True
    assert appointment.c.end_at.type.__class__.__name__ == "DateTime"
    assert cast(DateTime, appointment.c.end_at.type).timezone is True
    assert isinstance(appointment.c.status.type, String)
    assert appointment.c.status.type.length == 20
    assert appointment.c.created_at.type.__class__.__name__ == "DateTime"
    assert cast(DateTime, appointment.c.created_at.type).timezone is True
    assert appointment.c.created_at.nullable is False
    assert appointment.c.created_at.server_default is None
    assert appointment.c.updated_at.type.__class__.__name__ == "DateTime"
    assert cast(DateTime, appointment.c.updated_at.type).timezone is True
    assert appointment.c.updated_at.nullable is False
    assert appointment.c.updated_at.server_default is None

    # Foreign keys en appointment con ondelete="RESTRICT"
    fk_patient = next(fk for fk in appointment.foreign_keys if fk.column.table.name == "patient")
    assert fk_patient.ondelete == "RESTRICT"
    fk_prof = next(fk for fk in appointment.foreign_keys if fk.column.table.name == "professional")
    assert fk_prof.ondelete == "RESTRICT"
    fk_chair = next(fk for fk in appointment.foreign_keys if fk.column.table.name == "chair")
    assert fk_chair.ondelete == "RESTRICT"
    fk_service = next(fk for fk in appointment.foreign_keys if fk.column.table.name == "service")
    assert fk_service.ondelete == "RESTRICT"

    assert {
        constraint.name for constraint in appointment.constraints
    } >= {
        "ck_appointment_status",
        "ck_appointment_interval_order",
    }
    assert {
        index.name for index in appointment.indexes
    } >= {
        "ix_appointment_professional_id_start_at",
        "ix_appointment_chair_id_start_at",
        "ix_appointment_status_start_at",
    }

    # AppointmentStatusChangeModel
    assert status_change.c.id.type.__class__.__name__ == "Uuid"
    assert status_change.c.appointment_id.type.__class__.__name__ == "Uuid"
    assert status_change.c.from_status.nullable is True
    assert isinstance(status_change.c.from_status.type, String)
    assert status_change.c.from_status.type.length == 20
    assert status_change.c.to_status.nullable is False
    assert isinstance(status_change.c.to_status.type, String)
    assert status_change.c.to_status.type.length == 20
    assert status_change.c.changed_by.type.__class__.__name__ == "Uuid"
    assert status_change.c.changed_at.type.__class__.__name__ == "DateTime"
    assert cast(DateTime, status_change.c.changed_at.type).timezone is True
    assert status_change.c.note.nullable is True
    assert isinstance(status_change.c.note.type, String)
    assert status_change.c.note.type.length == 500

    # 8 columnas de reschedule
    reschedule_columns = [
        "reschedule_previous_start_at",
        "reschedule_previous_end_at",
        "reschedule_new_start_at",
        "reschedule_new_end_at",
        "reschedule_previous_professional_id",
        "reschedule_new_professional_id",
        "reschedule_previous_chair_id",
        "reschedule_new_chair_id",
    ]
    for col_name in reschedule_columns:
        col = status_change.c[col_name]
        assert col.nullable is True

    fk_app = next(fk for fk in status_change.foreign_keys if fk.parent.name == "appointment_id")
    assert fk_app.column.table.name == "appointment"
    assert fk_app.ondelete == "RESTRICT"

    assert {
        constraint.name for constraint in status_change.constraints
    } >= {
        "ck_appointment_status_change_from_status",
        "ck_appointment_status_change_to_status",
        "ck_appointment_status_change_reschedule_all_or_none",
    }
    assert {
        index.name for index in status_change.indexes
    } >= {
        "ix_appointment_status_change_appointment_id_changed_at",
    }


def test_user_model_registers_expected_columns_and_constraints() -> None:
    from app.db import models

    user = cast(Table, models.UserModel.__table__)

    assert user.name == "app_user"
    assert list(user.c.keys()) == [
        "id",
        "username",
        "display_name",
        "password_hash",
        "role",
        "professional_id",
        "active",
    ]
    assert user.c.id.type.__class__.__name__ == "Uuid"
    for column, length in (
        ("username", 150),
        ("display_name", 255),
        ("password_hash", 255),
        ("role", 20),
    ):
        column_type = user.c[column].type
        assert isinstance(column_type, String)
        assert column_type.length == length
        assert user.c[column].nullable is False
    assert user.c.professional_id.type.__class__.__name__ == "Uuid"
    assert user.c.professional_id.nullable is True
    assert user.c.active.nullable is False
    assert user.c.active.server_default is not None

    foreign_key = next(iter(user.c.professional_id.foreign_keys))
    assert foreign_key.column.table.name == "professional"
    assert foreign_key.ondelete == "RESTRICT"

    assert {constraint.name for constraint in user.constraints} >= {
        "ck_app_user_role",
        "ck_app_user_username_format",
        "ck_app_user_professional_by_role",
        "fk_app_user_professional_id_professional",
    }
    unique_indexes = {index.name for index in user.indexes if index.unique}
    assert unique_indexes == {"ux_app_user_username", "ux_app_user_professional_id"}
