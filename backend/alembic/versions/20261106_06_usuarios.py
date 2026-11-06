"""Add app_user table for authentication and roles.

Revision ID: 20261106_06_usuarios
Revises: 20261105_05_historial_sin_truncate
Create Date: 2026-11-06

"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261106_06_usuarios"
down_revision: Union[str, None] = "20261105_05_historial_sin_truncate"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("professional_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint(
            "role IN ('odontologo', 'recepcion', 'administrador')",
            name=op.f("ck_app_user_role"),
        ),
        sa.CheckConstraint(
            "username ~ '^[a-z0-9._-]{3,150}$'",
            name=op.f("ck_app_user_username_format"),
        ),
        sa.CheckConstraint(
            "(role = 'odontologo' AND professional_id IS NOT NULL) "
            "OR (role <> 'odontologo' AND professional_id IS NULL)",
            name=op.f("ck_app_user_professional_by_role"),
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["professional.id"],
            name=op.f("fk_app_user_professional_id_professional"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_user")),
    )
    op.create_index("ux_app_user_username", "app_user", ["username"], unique=True)
    op.create_index(
        "ux_app_user_professional_id",
        "app_user",
        ["professional_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_app_user_professional_id", table_name="app_user")
    op.drop_index("ux_app_user_username", table_name="app_user")
    op.drop_table("app_user")
