"""Persist working hours and agenda blocks.

Revision ID: 20261104_03_horarios_y_bloqueos
Revises: 20261103_02_catalogos_y_pacientes
Create Date: 2026-11-04

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261104_03_horarios_y_bloqueos"
down_revision: Union[str, None] = "20261103_02_catalogos_y_pacientes"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "working_hours",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("professional_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("end_minute", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "weekday >= 1 AND weekday <= 7",
            name=op.f("ck_working_hours_weekday_range"),
        ),
        sa.CheckConstraint(
            "start_minute >= 0 AND end_minute <= 1440 AND start_minute < end_minute",
            name=op.f("ck_working_hours_minute_range"),
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["professional.id"],
            name=op.f("fk_working_hours_professional_id_professional"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_working_hours")),
        sa.UniqueConstraint(
            "professional_id",
            "weekday",
            "start_minute",
            name=op.f("uq_working_hours_professional_weekday_start"),
        ),
    )
    op.create_index(
        "ix_working_hours_professional_id_weekday",
        "working_hours",
        ["professional_id", "weekday"],
        unique=False,
    )
    op.create_table(
        "block",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("professional_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "start_at < end_at",
            name=op.f("ck_block_interval_order"),
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["professional.id"],
            name=op.f("fk_block_professional_id_professional"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_block")),
    )
    op.create_index(
        "ix_block_professional_id_start_at_end_at",
        "block",
        ["professional_id", "start_at", "end_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_block_professional_id_start_at_end_at", table_name="block")
    op.drop_table("block")
    op.drop_index(
        "ix_working_hours_professional_id_weekday",
        table_name="working_hours",
    )
    op.drop_table("working_hours")
