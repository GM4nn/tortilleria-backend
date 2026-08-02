# datetime
from datetime import date, datetime, timedelta

# sqlalchemy
from sqlalchemy import exists, func
from sqlalchemy.orm import Session

# app
from app.core.constants import (
    mexico_now,
    ORDER_STATUSES_PENDING,
    ORDER_STATUSES_COMPLETE,
    ORDER_STATUSES_CANCEL,
    PAYMENT_STATUS_UNPAID,
    PAYMENT_STATUS_PARTIAL,
    PAYMENT_STATUS_PAID,
)
from app.src.models import Customer, Order, OrderDetail, OrderRefund, Product
from app.src.providers.pagination import PaginationProvider
from app.src.schemas.order import CompleteOrderInput, OrderCreate, PaginatedOrders
from app.src.services.firestore import firestore_service


class OrderProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def _to_dict(self, order: Order) -> dict:
        return {
            "id": order.id,
            "date": order.date,
            "total": order.total,
            "customer_id": order.customer_id,
            "status": order.status,
            "completed_at": order.completed_at,
            "notes": order.notes,
            "amount_paid": order.amount_paid or 0.0,
            "payment_status": order.payment_status,
            "default_dealer": order.default_dealer,
            "details": [
                {
                    "product_id": d.product_id,
                    "product_name": d.product.name if d.product else "N/A",
                    "quantity": d.quantity,
                    "unit_price": d.unit_price,
                    "subtotal": d.subtotal,
                }
                for d in order.order_details
            ],
            "refunds": [
                {
                    "product_id": r.product_id,
                    "product_name": r.product.name if r.product else "N/A",
                    "quantity": r.quantity,
                    "comments": r.comments,
                    "created_at": r.created_at,
                }
                for r in order.refunds
            ],
        }

    def _get(self, order_id: int) -> Order:
        order = self._db_session.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Pedido no encontrado")
        return order

    def get_by_id(self, order_id: int) -> dict:
        return self._to_dict(self._get(order_id))

    def get_all(self, offset: int = 0, limit: int | None = None, filters=None) -> list[dict]:
        query = self._db_session.query(Order)

        if filters:
            query = query.filter(*filters)

        query = query.order_by(Order.date.desc())

        if limit is not None:
            query = query.offset(offset).limit(limit)

        return [self._to_dict(order) for order in query.all()]

    def get_count(self, filters=None) -> int:
        query = self._db_session.query(func.count(Order.id))
        if filters:
            query = query.filter(*filters)
        return query.scalar() or 0

    def get_all_paginated(self, offset: int = 0, limit: int = 10, filters=None) -> PaginatedOrders:
        pagination = PaginationProvider(self._db_session).get_pagination_data(
            Order, offset, limit, filters
        )
        data = self.get_all(offset=offset, limit=limit, filters=filters)
        return PaginatedOrders(pagination=pagination, data=data)

    def build_status_filter(self, status: str):
        return [Order.status == status]

    def build_customer_filter(self, customer_id: int):
        return [Order.customer_id == customer_id]

    def build_dealer_filter(self, dealer: str):
        return [Order.default_dealer == dealer]

    def build_has_refunds_filter(self, has_refunds: bool):
        refund_exists = exists().where(OrderRefund.order_id == Order.id)
        return [refund_exists] if has_refunds else [~refund_exists]

    def build_payment_status_filter(self, payment_status: str):
        paid = func.coalesce(Order.amount_paid, 0.0)

        if payment_status == PAYMENT_STATUS_UNPAID:
            return [paid <= 0]
        if payment_status == PAYMENT_STATUS_PARTIAL:
            return [paid > 0, paid < Order.total]
        if payment_status == PAYMENT_STATUS_PAID:
            return [paid >= Order.total]
        return []

    def build_date_range_filter(self, start_date: date | None = None, end_date: date | None = None):
        filters = []
        if start_date:
            filters.append(
                Order.date >= datetime(start_date.year, start_date.month, start_date.day)
            )
        if end_date:
            end = datetime(end_date.year, end_date.month, end_date.day) + timedelta(days=1)
            filters.append(Order.date < end)
        return filters

    def create(self, data: OrderCreate) -> dict:
        customer = self._db_session.query(Customer).filter(
            Customer.id == data.customer_id
        ).first()
        if not customer:
            raise ValueError("Cliente no encontrado")

        fs_items: list[dict] = []
        total: float = 0.0
        details: list[OrderDetail] = []

        for item in data.items:
            product = self._db_session.query(Product).filter(
                Product.id == item.product_id
            ).first()
            if not product:
                raise ValueError(f"Producto {item.product_id} no encontrado")

            subtotal = item.quantity * item.unit_price
            total += subtotal

            details.append(OrderDetail(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=subtotal,
            ))
            fs_items.append({
                "product_id": product.id,
                "name": product.name,
                "price": item.unit_price,
                "quantity": item.quantity,
                "subtotal": subtotal,
            })

        if data.amount_paid > total:
            raise ValueError("El anticipo no puede exceder el total")

        order = Order(
            total=total,
            customer_id=data.customer_id,
            status=ORDER_STATUSES_PENDING,
            notes=data.notes,
            amount_paid=data.amount_paid,
            default_dealer=data.default_dealer,
        )
        order.order_details = details
        self._db_session.add(order)
        self._db_session.commit()
        self._db_session.refresh(order)

        firestore_service.add_order(
            order_id=order.id,
            customer_name=customer.customer_name,
            items=fs_items,
            total=total,
            amount_paid=data.amount_paid,
            created_at=order.date.isoformat() if order.date else mexico_now().isoformat(),
            default_dealer=data.default_dealer,
        )
        return self._to_dict(order)

    def register_payment(self, order_id: int, amount: float) -> dict:
        order = self._get(order_id)
        new_paid = (order.amount_paid or 0.0) + amount
        if new_paid > order.total:
            raise ValueError(f"El monto excede el total del pedido (${order.total:.2f})")
        order.amount_paid = new_paid
        self._db_session.commit()
        firestore_service.sync_payment(order_id, new_paid)
        return self._to_dict(order)

    def complete_order(self, order_id: int, data: CompleteOrderInput) -> dict:
        order = self._get(order_id)

        if data.final_payment > 0:
            order.amount_paid = (order.amount_paid or 0.0) + data.final_payment

        if round(order.amount_paid or 0.0, 2) != round(order.total, 2):
            raise ValueError(
                f"El pedido no está completamente pagado. "
                f"Pagado: ${order.amount_paid or 0.0:.2f}, Total: ${order.total:.2f}"
            )

        for item in data.refund_items:
            self._db_session.add(OrderRefund(
                order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                comments=item.comments,
            ))

        order.status = ORDER_STATUSES_COMPLETE
        order.completed_at = mexico_now()
        self._db_session.commit()
        firestore_service.update_order_status(order_id, ORDER_STATUSES_COMPLETE)
        return self._to_dict(order)

    def cancel(self, order_id: int) -> dict:
        order = self._get(order_id)
        order.status = ORDER_STATUSES_CANCEL
        self._db_session.commit()
        firestore_service.update_order_status(order_id, ORDER_STATUSES_CANCEL)
        return self._to_dict(order)
