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
from app.src.models import (
    Customer,
    CustomerProductPrice,
    Order,
    OrderDetail,
    OrderRefund,
    Product,
)
from app.src.providers.pagination import PaginationProvider
from app.src.schemas.order import CompleteOrderInput, OrderCreate, PaginatedOrders
from app.src.services.firestore import firestore_service
from app.src.services.ws_manager import ws_manager


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
                    "grammage": d.grammage,
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

    def build_catalog(self, customer_id: int) -> list[dict]:
        """Catálogo de productos activos con el precio resuelto para el cliente
        (precio personalizado si existe, si no el del producto). Se manda en el
        doc del pedido para que el repartidor pueda AGREGAR productos en la móvil."""
        products = (
            self._db_session.query(Product)
            .filter(Product.active.is_(True))
            .order_by(Product.display_order, Product.name)
            .all()
        )
        custom = {
            c.product_id: c.custom_price
            for c in self._db_session.query(CustomerProductPrice)
            .filter(CustomerProductPrice.customer_id == customer_id)
            .all()
        }
        return [
            {
                "product_id": p.id,
                "name": p.name,
                "icon": p.icon,
                "price": custom.get(p.id, p.price),
            }
            for p in products
        ]

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

        query = query.order_by(Order.date.desc(), Order.id.desc())

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
                grammage=item.grammage,
            ))
            fs_items.append({
                "product_id": product.id,
                "name": product.name,
                "price": item.unit_price,
                "quantity": item.quantity,
                "subtotal": subtotal,
                "grammage": item.grammage,
            })

        if data.amount_paid > total:
            raise ValueError("El anticipo no puede exceder el total")

        order_kwargs = dict(
            total=total,
            customer_id=data.customer_id,
            status=ORDER_STATUSES_PENDING,
            notes=data.notes,
            amount_paid=data.amount_paid,
            default_dealer=data.default_dealer,
            scheduled_order_id=data.scheduled_order_id,
        )
        if data.date is not None:
            order_kwargs["date"] = data.date
        order = Order(**order_kwargs)
        order.order_details = details
        self._db_session.add(order)
        self._db_session.commit()
        self._db_session.refresh(order)

        route = customer.route
        try:
            firestore_service.add_order(
                order_id=order.id,
                customer_name=customer.customer_name,
                customer_id=customer.id,
                items=fs_items,
                total=total,
                amount_paid=data.amount_paid,
                created_at=order.date.isoformat() if order.date else mexico_now().isoformat(),
                default_dealer=data.default_dealer,
                notes=data.notes,
                customer_lat=customer.latitude,
                customer_lng=customer.longitude,
                customer_direction=customer.customer_direction,
                route_id=customer.route_id,
                route_name=route.name if route else None,
                route_color=route.color if route else None,
                route_dealers=route.dealer_usernames if route else [],
            )
        except Exception as exc:
            print(f"[Order #{order.id}] Error sync Firestore: {exc}")
        return self._to_dict(order)

    # -------- acciones desde la app móvil (guardan en SQLite; la móvil ya
    # actualizó Firestore para el mapa en tiempo real) --------

    def set_notes(self, order_id: int, notes: str | None) -> dict:
        order = self._get(order_id)
        order.notes = notes or None
        self._db_session.commit()
        ws_manager.notify("orders")
        return self._to_dict(order)

    def set_amount_paid(self, order_id: int, amount: float) -> dict:
        """Fija el TOTAL pagado (no suma). Puede ser mayor al total (cambio)."""
        order = self._get(order_id)
        order.amount_paid = round(float(amount), 2) if float(amount) > 0 else 0.0
        self._db_session.commit()
        ws_manager.notify("orders")
        return self._to_dict(order)

    def apply_delivery(
        self, order_id: int, items: list[dict], total: float, amount_paid: float,
        complete: bool = True,
    ) -> dict:
        """Guarda la entrega desde el móvil: kilos entregados/devueltos (crea el
        detalle si es un producto agregado), total neto y pago. Si complete=True
        marca el pedido como completado; si es False solo guarda (sigue pendiente)."""
        order = self._get(order_id)
        detail_pool = list(order.order_details)
        used = set()

        def find_detail(pid: int):
            for i, d in enumerate(detail_pool):
                if d.product_id == pid and i not in used:
                    used.add(i)
                    return d
            return None

        for it in items:
            pid = it.get("product_id")
            if pid is None:
                continue
            qty = float(it.get("quantity") or 0.0)
            d = find_detail(pid)
            if d is None:
                if qty <= 0:
                    continue
                price = float(it.get("price") or 0.0)
                gram = float(it.get("grammage") or 0)
                d = OrderDetail(product_id=pid, quantity=qty, unit_price=price,
                                subtotal=round(qty * price, 2), grammage=gram)
                order.order_details.append(d)
            else:
                price = float(it.get("price") or d.unit_price or 0.0)
                d.quantity = qty
                d.unit_price = price
                d.subtotal = round(qty * price, 2)
                d.grammage = float(it.get("grammage") or 0)

        # Devoluciones (se reconstruyen desde 'returned')
        self._db_session.query(OrderRefund).filter(
            OrderRefund.order_id == order.id
        ).delete(synchronize_session=False)
        for it in items:
            ret = float(it.get("returned") or 0.0)
            if ret > 0:
                self._db_session.add(OrderRefund(
                    order_id=order.id, product_id=it.get("product_id"), quantity=ret,
                ))

        order.total = round(float(total), 2)
        paid = min(round(float(amount_paid), 2), round(order.total, 2))
        order.amount_paid = paid if paid > 0 else 0.0
        if complete:
            order.status = ORDER_STATUSES_COMPLETE
            if not order.completed_at:
                order.completed_at = mexico_now()
        self._db_session.commit()
        ws_manager.notify("orders")
        return self._to_dict(order)

    def register_payment(self, order_id: int, amount: float) -> dict:
        """Registra un abono. Puede exceder el total (el cambio queda registrado)."""
        order = self._get(order_id)
        new_paid = (order.amount_paid or 0.0) + amount
        order.amount_paid = round(new_paid, 2)
        self._db_session.commit()
        firestore_service.sync_payment(order_id, order.amount_paid)
        ws_manager.notify("orders")
        return self._to_dict(order)

    def complete_order(self, order_id: int, data: CompleteOrderInput) -> dict:
        order = self._get(order_id)

        # Se puede completar aunque no esté pagado; el pago final es opcional
        if data.final_payment > 0:
            new_paid = (order.amount_paid or 0.0) + data.final_payment
            order.amount_paid = round(new_paid, 2)

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
        ws_manager.notify("orders")
        return self._to_dict(order)

    def cancel(self, order_id: int) -> dict:
        order = self._get(order_id)
        order.status = ORDER_STATUSES_CANCEL
        self._db_session.commit()
        firestore_service.update_order_status(order_id, ORDER_STATUSES_CANCEL)
        ws_manager.notify("orders")
        return self._to_dict(order)

    def get_pending_delivery(self) -> list[dict]:
        """Órdenes pendientes de entrega o pago parcial (no completadas)."""
        orders = self._db_session.query(Order).filter(
            Order.status == ORDER_STATUSES_PENDING,
            Order.amount_paid < Order.total,
        ).order_by(Order.date.desc()).all()
        return [self._to_dict(o) for o in orders]

    def complete_all(self, order_ids: list[int]) -> dict:
        """Marca como completadas y pagas todas las órdenes indicadas."""
        completed = 0
        total_paid = 0.0
        for oid in order_ids:
            order = self._db_session.query(Order).filter(Order.id == oid).first()
            if not order:
                continue
            order.status = ORDER_STATUSES_COMPLETE
            order.amount_paid = round(order.total, 2)
            if not order.completed_at:
                order.completed_at = mexico_now()
            firestore_service.update_order_status(oid, ORDER_STATUSES_COMPLETE)
            firestore_service.sync_payment(oid, order.amount_paid)
            completed += 1
            total_paid += order.amount_paid
        self._db_session.commit()
        ws_manager.notify("orders")
        return {"completed": completed, "total_paid": round(total_paid, 2)}
