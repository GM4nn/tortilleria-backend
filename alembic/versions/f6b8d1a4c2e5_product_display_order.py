"""product display_order

Revision ID: f6b8d1a4c2e5
Revises: e5a7c9d3b2f4
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6b8d1a4c2e5"
down_revision: Union[str, Sequence[str], None] = "e5a7c9d3b2f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "display_order", sa.Integer(), nullable=False, server_default="100"
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("display_order")
