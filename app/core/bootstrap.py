# other libs
import csv
from pathlib import Path

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import (
    CUSTOMER_CATEGORY_MOSTRADOR,
    CUSTOMER_MOSTRADOR_NAME,
    SUPPLIER_PRODUCT_TYPE_SERVICE,
)
from app.core.database import SessionLocal
from app.src.models import Customer, Product, Supplier, Supply

DEFAULT_DIR = Path(__file__).parent / "data" / "default"


def add_default_products(db: Session) -> None:
    if db.query(Product).count() > 0:
        return

    path = DEFAULT_DIR / "products.csv"
    if not path.exists():
        return

    with open(path, newline="", encoding="utf-8-sig") as f:
        products = [
            Product(
                icon=row["icon"],
                name=row["name"],
                price=float(row["price"]),
                active=True,
            )
            for row in csv.DictReader(f)
        ]

    db.add_all(products)
    db.commit()


def create_mostrador_customer(db: Session) -> None:
    exists = db.query(Customer).filter(
        Customer.customer_category == CUSTOMER_CATEGORY_MOSTRADOR,
        Customer.active.is_(True),
    ).first()
    if exists:
        return

    db.add(Customer(
        customer_name=CUSTOMER_MOSTRADOR_NAME,
        customer_category=CUSTOMER_CATEGORY_MOSTRADOR,
        active=True,
        active2=True,
    ))
    db.commit()


def ensure_default_supplies(db: Session) -> None:
    path = DEFAULT_DIR / "default_supplies.csv"
    if not path.exists():
        return

    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if db.query(Supply).filter(
                Supply.supply_name == row["supply_name"],
                Supply.is_default.is_(True),
            ).first():
                continue

            supplier = db.query(Supplier).filter(
                Supplier.supplier_name == row["supplier_name"],
                Supplier.is_default.is_(True),
            ).first()
            if not supplier:
                supplier = Supplier(
                    supplier_name=row["supplier_name"],
                    product_type=SUPPLIER_PRODUCT_TYPE_SERVICE,
                    active=True,
                    is_default=True,
                )
                db.add(supplier)
                db.flush()
            elif not supplier.is_default:
                supplier.is_default = True

            db.add(Supply(
                supply_name=row["supply_name"],
                supplier_id=supplier.id,
                unit=row["unit"],
                is_default=True,
            ))

    db.commit()


def add_default_supplies(db: Session) -> None:
    path = DEFAULT_DIR / "supplies.csv"
    if not path.exists():
        return

    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if db.query(Supply).filter(Supply.supply_name == row["supply_name"]).first():
                continue

            db.add(Supply(
                supply_name=row["supply_name"],
                supplier_id=None,  # sin proveedor; se asigna despues
                unit=row["unit"],
                is_default=False,
            ))

    db.commit()


def run_bootstrap() -> None:
    db = SessionLocal()
    try:
        add_default_products(db)
        create_mostrador_customer(db)
        ensure_default_supplies(db)   # Luz CFE / Gas Nieto (is_default, protegidos)
        add_default_supplies(db)      # insumos normales sin proveedor (deletables)
    finally:
        db.close()
