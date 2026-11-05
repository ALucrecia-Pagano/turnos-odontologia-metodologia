"""Persist appointments and appointment status change history.

Revision ID: 20261105_04_turnos_e_historial
Revises: 20261104_03_horarios_y_bloqueos
Create Date: 2026-11-05

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261105_04_turnos_e_historial"
down_revision: Union[str, None] = "20261104_03_horarios_y_bloqueos"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "appointment",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("patient_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("professional_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("chair_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("service_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name=op.f("ck_appointment_status"),
        ),
        sa.CheckConstraint(
            "start_at < end_at",
            name=op.f("ck_appointment_interval_order"),
        ),
        sa.ForeignKeyConstraint(
            ["chair_id"],
            ["chair.id"],
            name=op.f("fk_appointment_chair_id_chair"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patient.id"],
            name=op.f("fk_appointment_patient_id_patient"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["professional.id"],
            name=op.f("fk_appointment_professional_id_professional"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["service.id"],
            name=op.f("fk_appointment_service_id_service"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointment")),
    )
    op.create_index(
        "ix_appointment_chair_id_start_at",
        "appointment",
        ["chair_id", "start_at"],
        unique=False,
    )
    op.create_index(
        "ix_appointment_professional_id_start_at",
        "appointment",
        ["professional_id", "start_at"],
        unique=False,
    )
    op.create_index(
        "ix_appointment_status_start_at",
        "appointment",
        ["status", "start_at"],
        unique=False,
    )

    op.create_table(
        "appointment_status_change",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("appointment_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("changed_by", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column(
            "reschedule_previous_start_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_previous_end_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_new_start_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_new_end_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_previous_professional_id",
            sa.Uuid(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_new_professional_id",
            sa.Uuid(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_previous_chair_id",
            sa.Uuid(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "reschedule_new_chair_id",
            sa.Uuid(as_uuid=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            "from_status IS NULL OR from_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name=op.f("ck_appointment_status_change_from_status"),
        ),
        sa.CheckConstraint(
            "to_status IN ('reservado', 'confirmado', 'atendido', 'ausente', 'cancelado')",
            name=op.f("ck_appointment_status_change_to_status"),
        ),
        sa.CheckConstraint(
            "(reschedule_previous_start_at IS NULL AND reschedule_previous_end_at IS NULL AND "
            "reschedule_new_start_at IS NULL AND reschedule_new_end_at IS NULL AND "
            "reschedule_previous_professional_id IS NULL AND reschedule_new_professional_id IS NULL AND "
            "reschedule_previous_chair_id IS NULL AND reschedule_new_chair_id IS NULL) "
            "OR "
            "(reschedule_previous_start_at IS NOT NULL AND reschedule_previous_end_at IS NOT NULL AND "
            "reschedule_new_start_at IS NOT NULL AND reschedule_new_end_at IS NOT NULL AND "
            "reschedule_previous_professional_id IS NOT NULL AND reschedule_new_professional_id IS NOT NULL AND "
            "reschedule_previous_chair_id IS NOT NULL AND reschedule_new_chair_id IS NOT NULL)",
            name=op.f("ck_appointment_status_change_reschedule_all_or_none"),
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointment.id"],
            name=op.f("fk_appointment_status_change_appointment_id_appointment"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reschedule_new_chair_id"],
            ["chair.id"],
            name=op.f("fk_appointment_status_change_reschedule_new_chair_id_chair"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reschedule_new_professional_id"],
            ["professional.id"],
            name=op.f("fk_appointment_status_change_reschedule_new_professional_id_professional"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reschedule_previous_chair_id"],
            ["chair.id"],
            name=op.f("fk_appointment_status_change_reschedule_previous_chair_id_chair"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reschedule_previous_professional_id"],
            ["professional.id"],
            name=op.f("fk_appointment_status_change_reschedule_previous_professional_id_professional"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointment_status_change")),
    )
    op.create_index(
        "ix_appointment_status_change_appointment_id_changed_at",
        "appointment_status_change",
        ["appointment_id", "changed_at"],
        unique=False,
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_appointment_status_change_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'appointment_status_change is append-only: updates and deletes are forbidden';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER tr_appointment_status_change_append_only
        BEFORE UPDATE OR DELETE ON appointment_status_change
        FOR EACH ROW EXECUTE FUNCTION prevent_appointment_status_change_modification();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS tr_appointment_status_change_append_only ON appointment_status_change;
        DROP FUNCTION IF EXISTS prevent_appointment_status_change_modification();
        """
    )
    op.drop_index(
        "ix_appointment_status_change_appointment_id_changed_at",
        table_name="appointment_status_change",
    )
    op.drop_table("appointment_status_change")
    op.drop_index("ix_appointment_status_start_at", table_name="appointment")
    op.drop_index(
        "ix_appointment_professional_id_start_at",
        table_name="appointment",
    )
    op.drop_index("ix_appointment_chair_id_start_at", table_name="appointment")
    op.drop_table("appointment")

