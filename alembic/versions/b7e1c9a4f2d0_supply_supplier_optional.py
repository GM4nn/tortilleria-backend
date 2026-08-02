"""supply supplier optional

Revision ID: b7e1c9a4f2d0
Revises: 742cd1ddfa4e
Create Date: 2026-08-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e1c9a4f2d0"
down_revision: Union[str, Sequence[str], None] = "742cd1ddfa4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("supplies", schema=None) as batch_op:
        batch_op.alter_column("supplier_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("supplies", schema=None) as batch_op:
        batch_op.alter_column("supplier_id", existing_type=sa.Integer(), nullable=False)
