"""routes table + customer geo/route columns

Revision ID: b1c2d3e4f5a6
Revises: 2052bfa0f9b1
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "2052bfa0f9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("dealer_username", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["dealer_username"], ["dealers.username"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("route_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_customers_route_id", "routes", ["route_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.drop_constraint("fk_customers_route_id", type_="foreignkey")
        batch_op.drop_column("route_id")
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")
    op.drop_table("routes")
