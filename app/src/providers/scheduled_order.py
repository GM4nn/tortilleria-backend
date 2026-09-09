# datetime
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now
from app.src.models import (
    CustomerProductPrice,
    Order,
    Product,
    ScheduledOrder,
    ScheduledOrderItem,
)
from app.src.providers.order import OrderProvider
from app.src.schemas.order import OrderCreate, OrderItemInput
from app.src.schemas.scheduled_order import ScheduledOrderCreate, ScheduledOrderUpdate


class ScheduledOrderProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def _to_dict(self, sched: ScheduledOrder) -> dict:
        return {
            "id": sched.id,
            "customer_id": sched.customer_id,
            "customer_name": sched.customer.customer_name if sched.customer else "N/A",
            "delivery_time": sched.delivery_time,
            "default_dealer": sched.default_dealer,
            "active": sched.active,
            "items": [
                {"weekday": i.weekday, "product_id": i.product_id, "quantity": i.quantity}
                for i in sched.items
            ],
        }

    def get_all(self) -> list[dict]:
        rows = self._db_session.query(ScheduledOrder).order_by(ScheduledOrder.id).all()
        return [self._to_dict(s) for s in rows]

    def _get(self, scheduled_id: int) -> ScheduledOrder:
        sched = self._db_session.query(ScheduledOrder).filter(
            ScheduledOrder.id == scheduled_id
        ).first()
        if not sched:
            raise ValueError("Pedido programado no encontrado")
        return sched

    def create(self, data: ScheduledOrderCreate) -> dict:
        sched = ScheduledOrder(
            customer_id=data.customer_id,
            delivery_time=data.delivery_time or None,
            default_dealer=data.default_dealer or None,
            active=data.active,
        )
        sched.items = [
            ScheduledOrderItem(weekday=it.weekday, product_id=it.product_id, quantity=it.quantity)
            for it in data.items
        ]
        self._db_session.add(sched)
        self._db_session.commit()
        self._db_session.refresh(sched)
        return self._to_dict(sched)

    def update(self, scheduled_id: int, data: ScheduledOrderUpdate) -> dict:
        sched = self._get(scheduled_id)
        sched.customer_id = data.customer_id
        sched.delivery_time = data.delivery_time or None
        sched.default_dealer = data.default_dealer or None
        sched.active = data.active
        # Reemplaza los items (cascade delete-orphan borra los viejos)
        sched.items = [
            ScheduledOrderItem(weekday=it.weekday, product_id=it.product_id, quantity=it.quantity)
            for it in data.items
        ]
        self._db_session.commit()
        self._db_session.refresh(sched)
        return self._to_dict(sched)

    def delete(self, scheduled_id: int) -> None:
        sched = self._get(scheduled_id)
        self._db_session.delete(sched)
        self._db_session.commit()

    def _resolve_price(self, customer_id: int, product_id: int) -> float | None:
        cpp = self._db_session.query(CustomerProductPrice).filter(
            CustomerProductPrice.customer_id == customer_id,
            CustomerProductPrice.product_id == product_id,
        ).first()
        if cpp:
            return cpp.custom_price
        product = self._db_session.query(Product).filter(Product.id == product_id).first()
        return product.price if product else None

    def generate_todays_orders(self) -> dict:
        """Crea los pedidos reales de hoy desde las plantillas activas. Idempotente."""
        now = mexico_now()
        weekday = now.weekday()  # 0=lunes ... 6=domingo
        today = now.date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)

        scheduleds = self._db_session.query(ScheduledOrder).filter(
            ScheduledOrder.active.is_(True)
        ).all()

        created = 0
        skipped = 0
        for sched in scheduleds:
            day_items = [it for it in sched.items if it.weekday == weekday]
            if not day_items:
                continue

            # Idempotencia: ¿ya se generó hoy un pedido de esta plantilla?
            already = self._db_session.query(Order).filter(
                Order.scheduled_order_id == sched.id,
                Order.date >= day_start,
                Order.date < day_end,
            ).first()
            if already:
                skipped += 1
                continue

            order_items: list[OrderItemInput] = []
            for it in day_items:
                price = self._resolve_price(sched.customer_id, it.product_id)
                if price is None or price <= 0:
                    continue
                order_items.append(OrderItemInput(
                    product_id=it.product_id, quantity=it.quantity, unit_price=price,
                ))
            if not order_items:
                continue

            dealer = sched.default_dealer
            if not dealer and sched.customer and sched.customer.route:
                dealer = sched.customer.route.dealer_username

            OrderProvider(self._db_session).create(OrderCreate(
                customer_id=sched.customer_id,
                default_dealer=dealer,
                scheduled_order_id=sched.id,
                items=order_items,
            ))
            created += 1

        return {"created": created, "skipped": skipped, "weekday": weekday}
