"""scheduled orders (recurring templates) + orders.scheduled_order_id

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-09-07 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scheduled_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("delivery_time", sa.String(length=5), nullable=True),
        sa.Column("default_dealer", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["default_dealer"], ["dealers.username"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scheduled_order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scheduled_order_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["scheduled_order_id"], ["scheduled_orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("scheduled_order_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_orders_scheduled_order_id", "scheduled_orders", ["scheduled_order_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_constraint("fk_orders_scheduled_order_id", type_="foreignkey")
        batch_op.drop_column("scheduled_order_id")
    op.drop_table("scheduled_order_items")
    op.drop_table("scheduled_orders")
