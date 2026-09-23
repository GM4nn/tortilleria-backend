# datetime
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now
from app.src.models import (
    Customer,
    CustomerProductPrice,
    Order,
    Product,
    ScheduledOrder,
    ScheduledOrderItem,
)
from app.src.providers.order import OrderProvider
from app.src.schemas.order import OrderCreate, OrderItemInput
from app.src.schemas.scheduled_order import ScheduledOrderCreate, ScheduledOrderUpdate
from app.src.services.firestore import firestore_service


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
        """Crea los pedidos reales de hoy desde las plantillas activas.

        Idempotente y "solo hoy":
        - Purga de Firestore cualquier pedido que NO sea de hoy (auto-repara si la
          limpieza de medianoche no corrió), para que no queden los de ayer sin
          completar mezclados con los nuevos.
        - Idempotencia POR CLIENTE: si un cliente ya tiene un pedido hoy (de esta u
          otra plantilla, o manual) no se le crea otro. Así nunca hay dos pedidos
          del mismo cliente en el día.
        """
        now = mexico_now()
        weekday = now.weekday()  # 0=lunes ... 6=domingo
        today = now.date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)

        # Borrar solo los de la SEMANA PASADA (no los de esta semana).
        # keep_date = inicio de esta semana (lunes), para no borrar pedidos de
        # lunes-domingo de la semana en curso.
        week_start = today - timedelta(days=weekday)
        firestore_service.clear_stale_orders(week_start.isoformat())

        # Clientes que YA tienen un pedido hoy (cualquier vía): no duplicarlos
        rows = self._db_session.query(Order.customer_id).filter(
            Order.date >= day_start,
            Order.date < day_end,
        ).all()
        customers_with_order: set[int] = {r[0] for r in rows}

        scheduleds = self._db_session.query(ScheduledOrder).filter(
            ScheduledOrder.active.is_(True)
        ).all()

        created = 0
        skipped = 0
        errors = 0
        for sched in scheduleds:
            day_items = [it for it in sched.items if it.weekday == weekday]
            if not day_items:
                continue

            # El cliente pudo haberse borrado/desactivado y dejar el programado
            # huérfano: sáltalo en vez de reventar toda la generación.
            customer = sched.customer
            if customer is None or not getattr(customer, "active", True):
                skipped += 1
                continue

            # Idempotencia por CLIENTE: si ya tiene un pedido hoy, no crear otro.
            if sched.customer_id in customers_with_order:
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

            # Repartidor: el explícito de la plantilla; si no, el de la ruta cuando
            # es UNO solo. Si la ruta tiene varios, queda sin asignar y cualquiera
            # de la ruta lo toma en el móvil.
            dealer = sched.default_dealer
            if not dealer and customer.route:
                route_dealers = customer.route.dealer_usernames
                dealer = route_dealers[0] if len(route_dealers) == 1 else None

            try:
                OrderProvider(self._db_session).create(OrderCreate(
                    customer_id=sched.customer_id,
                    default_dealer=dealer,
                    scheduled_order_id=sched.id,
                    items=order_items,
                ))
            except Exception as exc:  # noqa: BLE001
                # Un programado con problema no debe tumbar los demás.
                self._db_session.rollback()
                errors += 1
                print(f"[Programados] Error generando pedido de plantilla "
                      f"#{sched.id} (cliente {sched.customer_id}): {exc}")
                continue

            customers_with_order.add(sched.customer_id)  # no duplicar en esta corrida
            created += 1

        return {"created": created, "skipped": skipped, "errors": errors, "weekday": weekday}

    def generate_for_customer(self, customer_id: int, dealer: str | None = None) -> dict:
        """Genera el pedido de HOY para UN cliente (al tocarlo en gris en el mapa).
        Usa su plantilla del día si la tiene; si no, crea un pedido vacío para
        agregar productos a mano. Idempotente: si ya tiene pedido hoy, lo devuelve."""
        now = mexico_now()
        weekday = now.weekday()
        today = now.date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)

        existing = self._db_session.query(Order).filter(
            Order.customer_id == customer_id,
            Order.date >= day_start,
            Order.date < day_end,
        ).first()
        if existing:
            return {"created": False, "order_id": existing.id, "reason": "already"}

        customer = self._db_session.query(Customer).filter(
            Customer.id == customer_id
        ).first()
        if customer is None or not getattr(customer, "active", True):
            raise ValueError("Cliente no encontrado o inactivo")

        sched = self._db_session.query(ScheduledOrder).filter(
            ScheduledOrder.customer_id == customer_id,
            ScheduledOrder.active.is_(True),
        ).first()

        order_items: list[OrderItemInput] = []
        if sched:
            for it in sched.items:
                if it.weekday != weekday:
                    continue
                price = self._resolve_price(customer_id, it.product_id)
                if price is None or price <= 0:
                    continue
                order_items.append(OrderItemInput(
                    product_id=it.product_id, quantity=it.quantity, unit_price=price,
                ))

        # Repartidor: el que lo solicitó; si no, la plantilla; si no, la ruta (si es 1)
        resolved = dealer or (sched.default_dealer if sched else None)
        if not resolved and customer.route:
            rd = customer.route.dealer_usernames
            resolved = rd[0] if len(rd) == 1 else None

        order = OrderProvider(self._db_session).create(OrderCreate(
            customer_id=customer_id,
            default_dealer=resolved,
            scheduled_order_id=sched.id if sched else None,
            items=order_items,
        ))
        return {"created": True, "order_id": order["id"], "empty": not order_items}
