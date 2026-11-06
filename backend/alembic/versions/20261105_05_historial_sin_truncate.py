"""Add truncate protection trigger on appointment_status_change.

Revision ID: 20261105_05_historial_sin_truncate
Revises: 20261105_04_turnos_e_historial
Create Date: 2026-11-05 11:35:00.000000
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20261105_05_historial_sin_truncate"
down_revision: str | None = "20261105_04_turnos_e_historial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TRIGGER tr_appointment_status_change_no_truncate
        BEFORE TRUNCATE ON appointment_status_change
        FOR EACH STATEMENT EXECUTE FUNCTION prevent_appointment_status_change_modification();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS tr_appointment_status_change_no_truncate ON appointment_status_change;
        """
    )
