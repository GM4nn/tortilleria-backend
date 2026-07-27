"""Datos de prueba para la SQLite de FastAPI.

BORRA TODO y recrea desde cero: esquema + base (clientes, productos,
repartidores) + ~6.5 meses de pedidos con estados/pagos/repartidores variados
(para probar filtros y paginación).

Uso (desde backend/, con el venv activado):
    python seed_data.py
"""

import random
from datetime import datetime, timedelta, date

import app.src.models  # noqa: F401  (registra TODAS las tablas en la metadata)
from app.core.base import Base
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.src.models import Customer, Dealer, Order, OrderDetail, Product

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


def reset_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


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


def main() -> None:
    print("=" * 50)
    print("SEED DATA (FastAPI SQLite) - RESET COMPLETO")
    print(f"Periodo: {START_DATE} -> {END_DATE}  ({DAYS_BACK} dias)")
    print(f"BD: {settings.DATABASE_URI}")
    print("=" * 50)

    print("\nBorrando TODO y recreando el esquema...")
    reset_schema()

    with SessionLocal() as db:
        customers, products, dealers = seed_base(db)
        print(f"  Base: {len(customers)} clientes, {len(products)} productos, {len(dealers)} repartidores")
        print("\nGenerando pedidos...")
        seed_orders(db, customers, products, dealers)

    print("\nListo.")


if __name__ == "__main__":
    main()
