"""Persist catalog entities and patients.

Revision ID: 20261103_02_catalogos_y_pacientes
Revises: 20261103_01_baseline
Create Date: 2026-11-04

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261103_02_catalogos_y_pacientes"
down_revision: Union[str, None] = "20261103_01_baseline"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
    )
    op.create_table(
        "professional",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("license_number", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_professional")),
    )
    op.create_table(
        "chair",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_normalized", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chair")),
    )
    op.create_index(
        "ux_chair_name_normalized",
        "chair",
        ["name_normalized"],
        unique=True,
    )
    op.create_table(
        "service",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_normalized", sa.String(length=255), nullable=False),
        sa.Column("default_duration_min", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service")),
    )
    op.create_index(
        "ux_service_name_normalized",
        "service",
        ["name_normalized"],
        unique=True,
    )
    op.create_table(
        "patient",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("dni", sa.String(length=8), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("health_insurance", sa.String(length=255), nullable=True),
        sa.CheckConstraint("dni ~ '^[0-9]{7,8}$'", name=op.f("ck_patient_dni_format")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patient")),
    )
    op.create_index("ux_patient_dni", "patient", ["dni"], unique=True)


def downgrade() -> None:
    op.drop_index("ux_patient_dni", table_name="patient")
    op.drop_table("patient")
    op.drop_index("ux_service_name_normalized", table_name="service")
    op.drop_table("service")
    op.drop_index("ux_chair_name_normalized", table_name="chair")
    op.drop_table("chair")
    op.drop_table("professional")
