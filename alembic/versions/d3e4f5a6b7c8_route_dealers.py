"""route_dealers: varios repartidores por ruta

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "route_dealers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("dealer_username", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.ForeignKeyConstraint(["dealer_username"], ["dealers.username"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # Sembrar la tabla con el repartidor "principal" actual de cada ruta
    op.execute(
        "INSERT INTO route_dealers (route_id, dealer_username) "
        "SELECT id, dealer_username FROM routes WHERE dealer_username IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_table("route_dealers")
