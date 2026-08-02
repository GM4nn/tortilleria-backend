"""Datos de prueba para la SQLite de FastAPI.

BORRA TODO y recrea desde cero: esquema + base (clientes, productos,
repartidores) + ~6.5 meses de pedidos con estados/pagos/repartidores variados
(para probar filtros y paginación).

Uso (desde backend/, con el venv activado):
    python seed_data.py
"""

import random
from datetime import datetime, timedelta, date

from sqlalchemy import func, inspect

import app.src.models  # noqa: F401  (registra TODAS las tablas en la metadata)
from app.core.base import Base
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.src.models import (
    CashCut,
    Customer,
    Dealer,
    Order,
    OrderDetail,
    Product,
    Sale,
    SaleDetail,
)

random.seed(42)

DAYS_BACK = 195  # ~6.5 meses
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=DAYS_BACK)

CUSTOMERS = [
    ("Abarrotes Don José", "Tienda"),
    ("Cocina Doña María", "Comedor"),
    ("Fonda La Abuela", "Comedor"),
    ("Lonchería El Buen Sabor", "Comedor"),
    ("Mini Super El Sol", "Tienda"),
    ("Restaurante El Fogón", "Comedor"),
    ("Taquería Los Amigos", "Comedor"),
    ("Tienda La Esquina", "Tienda"),
    ("Tiendita Lupita", "Tienda"),
    ("Cliente Mostrador", "Mostrador"),
]

PRODUCTS = [
    ("🌽", "Tortilla Kilo", 23.0),
    ("🫓", "Tortilla de Harina", 35.0),
    ("🥙", "Tostada", 18.0),
    ("🌮", "Totopos", 40.0),
    ("🧀", "Sope", 5.0),
    ("🫔", "Gordita", 8.0),
]

DEALERS = [
    ("ana", "1234", "Ana"),
    ("beto", "5678", "Beto"),
    ("juanito", "1111", "Juanito"),
    ("laura", "2222", "Laura"),
]

QUANTITIES = [0.5, 1, 1.5, 2, 3, 5, 10, 15]


def random_time(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, random.randint(7, 19), random.randint(0, 59))


def date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def reset_data(db) -> None:
    # Borra las filas (no las tablas) respetando las FKs: hijos -> padres
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


def seed_base(db):
    for name, category in CUSTOMERS:
        db.add(Customer(customer_name=name, customer_category=category))
    for icon, name, price in PRODUCTS:
        db.add(Product(icon=icon, name=name, price=price))
    for username, pin, name in DEALERS:
        db.add(Dealer(username=username, pin=pin, name=name))
    db.commit()
    return db.query(Customer).all(), db.query(Product).all(), db.query(Dealer).all()


def seed_orders(db, customers, products, dealers) -> None:
    max_items = min(4, len(products))
    dealer_usernames = [d.username for d in dealers] + [None, None]  # ~33% sin asignar
    order_count = 0
    paid = pending = partial = 0
    batch: list[tuple[Order, list]] = []

    for d in date_range(START_DATE, END_DATE):
        weekday = d.weekday()
        weights = [10, 40, 35, 15] if weekday < 6 else [45, 35, 15, 5]
        num_orders = random.choices([0, 1, 2, 3], weights=weights)[0]

        for _ in range(num_orders):
            customer = random.choice(customers)
            dt = random_time(d)

            selected = random.sample(products, random.randint(1, max_items))
            total = 0.0
            details = []
            for product in selected:
                qty = random.choice(QUANTITIES)
                subtotal = round(qty * product.price, 2)
                total += subtotal
                details.append((product, qty, subtotal))
            total = round(total, 2)

            status = random.choices(
                ["completado", "pendiente", "cancelado"], weights=[70, 20, 10]
            )[0]

            completed_at = None
            if status == "completado":
                amount_paid = total
                completed_at = dt + timedelta(minutes=random.randint(15, 120))
                paid += 1
            elif status == "cancelado":
                amount_paid = 0.0
            else:
                kind = random.choices(["sin", "parcial", "pagado"], weights=[45, 35, 20])[0]
                if kind == "sin":
                    amount_paid = 0.0
                    pending += 1
                elif kind == "parcial":
                    amount_paid = round(total * random.uniform(0.3, 0.7), 2)
                    partial += 1
                else:
                    amount_paid = total
                    paid += 1

            order = Order(
                date=dt,
                total=total,
                customer_id=customer.id,
                status=status,
                completed_at=completed_at,
                amount_paid=amount_paid,
                default_dealer=random.choice(dealer_usernames),
            )
            batch.append((order, details))
            order_count += 1

    BATCH_SIZE = 100
    for i in range(0, len(batch), BATCH_SIZE):
        chunk = batch[i:i + BATCH_SIZE]
        for order, _ in chunk:
            db.add(order)
        db.flush()
        for order, details in chunk:
            for product, qty, subtotal in details:
                db.add(OrderDetail(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.price,
                    subtotal=subtotal,
                ))
        db.flush()

    db.commit()
    print(f"  Pedidos creados: {order_count}")
    print(f"  Pagados: {paid}  ·  pendientes sin pagar: {pending}  ·  parciales: {partial}")


def seed_sales(db, mostrador, products) -> None:
    if mostrador is None or not products:
        print("  Sin cliente mostrador o productos; no se generan ventas.")
        return

    max_items = min(3, len(products))
    sale_qty = [0.5, 1, 1.5, 2, 3]
    sale_count = 0
    batch: list[tuple[Sale, list]] = []

    for d in date_range(START_DATE, END_DATE):
        weekday = d.weekday()
        num_sales = random.randint(8, 16) if weekday >= 5 else random.randint(5, 12)

        for _ in range(num_sales):
            dt = random_time(d)
            selected = random.sample(products, random.randint(1, max_items))
            total = 0.0
            details = []
            for product in selected:
                qty = random.choice(sale_qty)
                subtotal = round(qty * product.price, 2)
                total += subtotal
                details.append((product, qty, subtotal))

            sale = Sale(date=dt, total=round(total, 2), customer_id=mostrador.id)
            batch.append((sale, details))
            sale_count += 1

    BATCH_SIZE = 100
    for i in range(0, len(batch), BATCH_SIZE):
        chunk = batch[i:i + BATCH_SIZE]
        for sale, _ in chunk:
            db.add(sale)
        db.flush()
        for sale, details in chunk:
            for product, qty, subtotal in details:
                db.add(SaleDetail(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.price,
                    subtotal=subtotal,
                ))
        db.flush()

    db.commit()
    print(f"  Ventas creadas: {sale_count}")


def seed_cash_cuts(db) -> None:
    notes_options = [
        "Faltante sin identificar",
        "Error en cambio",
        "Se pago proveedor en efectivo",
        "Sobrante del dia anterior",
        "Diferencia por redondeo acumulado",
    ]
    cut_count = 0

    # Hasta ayer: el corte de HOY se deja sin cerrar para poder probarlo.
    for d in date_range(START_DATE, END_DATE - timedelta(days=1)):
        day_start = datetime(d.year, d.month, d.day)
        day_end = day_start + timedelta(days=1)

        sales_result = db.query(
            func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0.0)
        ).filter(Sale.date >= day_start, Sale.date < day_end).first()
        sales_count = sales_result[0] or 0
        sales_total = float(sales_result[1] or 0.0)

        orders_result = db.query(
            func.count(Order.id), func.coalesce(func.sum(Order.total), 0.0)
        ).filter(
            Order.status == "completado",
            Order.completed_at >= day_start,
            Order.completed_at < day_end,
        ).first()
        orders_count = orders_result[0] or 0
        orders_total = float(orders_result[1] or 0.0)

        if sales_count == 0 and orders_count == 0:
            continue

        expected_total = round(sales_total + orders_total, 2)

        variance = random.choices(["exact", "small", "notable"], weights=[70, 20, 10])[0]
        if variance == "exact":
            diff = 0.0
        elif variance == "small":
            diff = round(random.uniform(-20, 15), 2)
        else:
            diff = round(
                random.uniform(-80, -20) if random.random() < 0.7 else random.uniform(20, 50),
                2,
            )

        declared_total = round(expected_total + diff, 2)
        declared_cash = round(declared_total * random.uniform(0.60, 0.80), 2)
        declared_card = round(declared_total * random.uniform(0.10, 0.25), 2)
        declared_transfer = round(declared_total - declared_cash - declared_card, 2)

        db.add(CashCut(
            opened_at=datetime(d.year, d.month, d.day, 0, 0, 0),
            closed_at=datetime(d.year, d.month, d.day, random.randint(19, 20), random.randint(0, 59)),
            sales_count=sales_count,
            orders_count=orders_count,
            sales_total=sales_total,
            orders_total=orders_total,
            expected_total=expected_total,
            declared_cash=declared_cash,
            declared_card=declared_card,
            declared_transfer=declared_transfer,
            declared_total=declared_total,
            difference=diff,
            notes=random.choice(notes_options) if variance == "notable" else None,
        ))
        cut_count += 1

    db.commit()
    print(f"  Cortes de caja creados: {cut_count}")


def main() -> None:
    print("=" * 50)
    print("SEED DATA (FastAPI SQLite) - RESET DE DATOS")
    print(f"Periodo: {START_DATE} -> {END_DATE}  ({DAYS_BACK} dias)")
    print(f"BD: {settings.DATABASE_URI}")
    print("=" * 50)

    if not inspect(engine).has_table("orders"):
        print("\nEl esquema no existe. Corre primero:  alembic upgrade head")
        return

    with SessionLocal() as db:
        print("\nBorrando datos anteriores...")
        reset_data(db)

        customers, products, dealers = seed_base(db)
        print(f"  Base: {len(customers)} clientes, {len(products)} productos, {len(dealers)} repartidores")

        mostrador = next(
            (c for c in customers if (c.customer_category or "").lower() == "mostrador"),
            None,
        )

        print("\nGenerando pedidos...")
        seed_orders(db, customers, products, dealers)

        print("\nGenerando ventas de mostrador...")
        seed_sales(db, mostrador, products)

        print("\nGenerando cortes de caja...")
        seed_cash_cuts(db)

    print("\nListo.")


if __name__ == "__main__":
    main()
