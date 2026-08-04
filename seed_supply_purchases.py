"""Seed SOLO de compras de insumos (supply_purchases).

Regenera el historial de compras de cada insumo con ~6 compras espaciadas en el
tiempo y sobrantes realistas (para probar Historial / Períodos / consumo).
No toca el resto de tablas.

Uso (desde backend/, con el venv activado y el servidor DETENIDO):
    python seed_supply_purchases.py
"""

import random
from datetime import datetime, timedelta, date

from sqlalchemy import inspect

import app.src.models  # noqa: F401
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.src.models import Supplier, Supply, SupplyPurchase

random.seed(7)

DAYS_BACK = 240
END_DATE = date.today()
MIN_PURCHASES = 15
MAX_PURCHASES = 25


def seed(db) -> None:
    supplies = db.query(Supply).all()
    suppliers = db.query(Supplier).all()

    if not supplies:
        print("No hay insumos. Crea insumos primero (bootstrap / seed_data).")
        return
    if not suppliers:
        print("No hay proveedores. Crea proveedores primero.")
        return

    # Limpia las compras previas para regenerarlas de forma consistente
    borradas = db.query(SupplyPurchase).delete()
    db.commit()
    print(f"Compras previas borradas: {borradas}")

    total = 0
    for supply in supplies:
        supplier = supply.supplier or random.choice(suppliers)
        n = random.randint(MIN_PURCHASES, MAX_PURCHASES)

        # Fechas espaciadas, de la más antigua a la más nueva
        dates = sorted(
            END_DATE - timedelta(days=random.randint(1, DAYS_BACK)) for _ in range(n)
        )

        remaining = 0.0  # la primera compra no tiene sobrante previo
        for pdate in dates:
            qty = random.choice([20, 25, 30, 40, 50, 60])
            unit_price = round(random.uniform(5, 25), 2)
            db.add(SupplyPurchase(
                supply_id=supply.id,
                supplier_id=supplier.id,
                purchase_date=pdate,
                quantity=qty,
                unit=supply.unit,
                unit_price=unit_price,
                total_price=round(qty * unit_price, 2),
                remaining=round(remaining, 2),
                notes=None,
            ))
            # Sobra un poco para el próximo periodo
            remaining = round(random.uniform(0, qty * 0.3), 2)
            total += 1

    db.commit()
    print(f"Compras de insumos creadas: {total}  (en {len(supplies)} insumos)")


def main() -> None:
    print("=" * 50)
    print("SEED - COMPRAS DE INSUMOS")
    print(f"BD: {settings.DATABASE_URI}")
    print("=" * 50)

    if not inspect(engine).has_table("supply_purchases"):
        print("\nEl esquema no existe. Corre primero:  alembic upgrade head")
        return

    with SessionLocal() as db:
        seed(db)

    print("Listo.")


if __name__ == "__main__":
    main()
