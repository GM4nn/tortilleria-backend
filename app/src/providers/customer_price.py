# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.src.models import Customer, CustomerProductPrice, Order, OrderDetail
from app.src.services.firestore import firestore_service
from app.core.constants import ORDER_STATUSES_PENDING


class CustomerPriceProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_for_customer(self, customer_id: int) -> list[CustomerProductPrice]:
        return self._db_session.query(CustomerProductPrice).filter(
            CustomerProductPrice.customer_id == customer_id
        ).all()

    def _sync_customer(self, customer_id: int) -> None:
        customer = self._db_session.query(Customer).filter(
            Customer.id == customer_id
        ).first()
        if customer:
            self._db_session.refresh(customer, attribute_names=["product_prices"])
            firestore_service.upsert_customer(customer)

    def _sync_order(self, order: Order) -> None:
        if not order.customer:
            return
        fs_items = [
            {
                "product_id": d.product_id,
                "name": d.product.name if d.product else "N/A",
                "price": d.unit_price,
                "quantity": d.quantity,
                "subtotal": d.subtotal,
                "grammage": d.grammage,
            }
            for d in order.order_details
        ]
        firestore_service.sync_order_items(
            order.id, fs_items, order.total
        )

    def save_price(self, customer_id: int, product_id: int, price: float) -> CustomerProductPrice:
        existing = self._db_session.query(CustomerProductPrice).filter(
            CustomerProductPrice.customer_id == customer_id,
            CustomerProductPrice.product_id == product_id,
        ).first()

        if existing:
            existing.custom_price = price
        else:
            existing = CustomerProductPrice(
                customer_id=customer_id,
                product_id=product_id,
                custom_price=price,
            )
            self._db_session.add(existing)

        self._db_session.commit()
        self._db_session.refresh(existing)

        # Actualizar OrderDetail.unit_price de pedidos PENDIENTES
        pending = self._db_session.query(Order).filter(
            Order.customer_id == customer_id,
            Order.status == ORDER_STATUSES_PENDING,
        ).all()
        for order in pending:
            changed = False
            for detail in order.order_details:
                if detail.product_id == product_id:
                    detail.unit_price = price
                    detail.subtotal = round(detail.quantity * price, 2)
                    changed = True
            if changed:
                order.total = round(
                    sum(d.subtotal for d in order.order_details), 2
                )
                self._sync_order(order)
        self._db_session.commit()

        self._sync_customer(customer_id)
        return existing
