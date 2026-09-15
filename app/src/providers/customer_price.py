# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.src.models import Customer, CustomerProductPrice
from app.src.services.firestore import firestore_service


class CustomerPriceProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_for_customer(self, customer_id: int) -> list[CustomerProductPrice]:
        return self._db_session.query(CustomerProductPrice).filter(
            CustomerProductPrice.customer_id == customer_id
        ).all()

    def _sync_customer(self, customer_id: int) -> None:
        # Refleja el precio por cliente en Firestore (map 'prices' del cliente)
        customer = self._db_session.query(Customer).filter(
            Customer.id == customer_id
        ).first()
        if customer:
            firestore_service.upsert_customer(customer)

    def save_price(self, customer_id: int, product_id: int, price: float) -> CustomerProductPrice:
        existing = self._db_session.query(CustomerProductPrice).filter(
            CustomerProductPrice.customer_id == customer_id,
            CustomerProductPrice.product_id == product_id,
        ).first()

        if existing:
            existing.custom_price = price
            self._db_session.commit()
            self._db_session.refresh(existing)
            self._sync_customer(customer_id)
            return existing

        record = CustomerProductPrice(
            customer_id=customer_id,
            product_id=product_id,
            custom_price=price,
        )
        self._db_session.add(record)
        self._db_session.commit()
        self._db_session.refresh(record)
        self._sync_customer(customer_id)
        return record
