"""add grammage to order_details

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_details",
        sa.Column("grammage", sa.Float(), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("order_details", "grammage")
