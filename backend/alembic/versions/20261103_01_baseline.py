"""Create the empty baseline revision.

Revision ID: 20261103_01_baseline
Revises:
Create Date: 2026-11-03

"""
from typing import Union


revision: str = "20261103_01_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
