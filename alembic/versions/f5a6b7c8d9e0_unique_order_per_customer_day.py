"""un pedido activo por cliente por dia (bloqueo duro anti-duplicados)

Revision ID: f5a6b7c8d9e0
Revises: a1b2c3d4e5f6
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indice unico parcial: nunca 2 pedidos ACTIVOS (no cancelados) del mismo
    # cliente el mismo dia calendario. Cancelar uno libera el dia para otro.
    # Si ya existieran filas duplicadas en produccion, esta migracion fallaria
    # al crear el indice (a proposito: obliga a resolverlas a mano primero).
    op.create_index(
        "uq_order_customer_active_day",
        "orders",
        ["customer_id", sa.text("date(date)")],
        unique=True,
        sqlite_where=sa.text("status != 'cancelado'"),
    )


def downgrade() -> None:
    op.drop_index("uq_order_customer_active_day", table_name="orders")
