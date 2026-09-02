# other libs
import csv
from pathlib import Path

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import (
    CUSTOMER_CATEGORY_MOSTRADOR,
    CUSTOMER_MOSTRADOR_NAME,
)
from app.core.database import SessionLocal
from app.src.models import Customer, Product

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
                code=row.get("code") or None,
                is_default=(row.get("is_default", "").strip().lower() == "true"),
                display_order=int(row.get("display_order") or 0),
            )
            for row in csv.DictReader(f)
        ]

    db.add_all(products)
    db.commit()


def create_mostrador_customer(db: Session) -> None:
    exists = db.query(Customer).filter(
        Customer.customer_category == CUSTOMER_CATEGORY_MOSTRADOR,
        Customer.active.is_(True),
        Customer.active2.is_(False),
    ).first()
    if exists:
        return

    db.add(Customer(
        customer_name=CUSTOMER_MOSTRADOR_NAME,
        customer_category=CUSTOMER_CATEGORY_MOSTRADOR,
        active=True,
        active2=False,
    ))
    db.commit()


def run_bootstrap() -> None:
    db = SessionLocal()
    try:
        add_default_products(db)
        create_mostrador_customer(db)
    finally:
        db.close()
