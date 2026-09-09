# std
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import ORDER_STATUSES_PENDING, mexico_now
from app.src.models import Customer, Order, Route
from app.src.schemas.route import RouteCreate, RouteUpdate
from app.src.services.firestore import firestore_service


class RouteProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def _reassign_todays_orders(
        self, route_id: int, new_dealer: str | None, old_dealer: str | None
    ) -> None:
        """Actualiza los pedidos de HOY (aún pendientes) de la ruta con el nuevo
        repartidor, en SQLite y Firestore, para que el móvil deje de mostrar
        'Tomar'. Solo toca los que están SIN repartidor o con el repartidor viejo
        de la ruta (no pisa un pedido que un repartidor ya tomó en el móvil)."""
        now = mexico_now()
        day_start = datetime(now.year, now.month, now.day)
        day_end = day_start + timedelta(days=1)

        orders = (
            self._db_session.query(Order)
            .join(Customer, Customer.id == Order.customer_id)
            .filter(
                Customer.route_id == route_id,
                Order.date >= day_start,
                Order.date < day_end,
                Order.status == ORDER_STATUSES_PENDING,
            )
            .all()
        )
        changed = [
            o
            for o in orders
            if o.default_dealer != new_dealer
            and (o.default_dealer is None or o.default_dealer == old_dealer)
        ]
        for order in changed:
            order.default_dealer = new_dealer
        if changed:
            self._db_session.commit()
            for order in changed:
                firestore_service.sync_dealer(order.id, new_dealer)

    def get_all(self) -> list[Route]:
        return self._db_session.query(Route)\
            .filter(Route.active.is_(True))\
            .order_by(Route.name)\
            .all()

    def get_by_id(self, route_id: int) -> Route:
        route = self._db_session.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise ValueError("Ruta no encontrada")
        return route

    def create(self, data: RouteCreate) -> Route:
        route = Route(
            name=data.name,
            color=data.color,
            dealer_username=data.dealer_username or None,
        )
        self._db_session.add(route)
        self._db_session.commit()
        self._db_session.refresh(route)
        return route

    def update(self, route_id: int, data: RouteUpdate) -> Route:
        route = self.get_by_id(route_id)
        old_dealer = route.dealer_username
        new_dealer = data.dealer_username or None
        route.name = data.name
        route.color = data.color
        route.dealer_username = new_dealer
        self._db_session.commit()
        # Propaga a los pedidos de hoy de la ruta (sin repartidor o con el viejo)
        self._reassign_todays_orders(route_id, new_dealer, old_dealer)
        self._db_session.refresh(route)
        return route

    def delete(self, route_id: int) -> None:
        route = self.get_by_id(route_id)
        # Los clientes de la ruta quedan sin ruta (no se borran)
        self._db_session.query(Customer).filter(Customer.route_id == route_id).update(
            {Customer.route_id: None}, synchronize_session=False
        )
        self._db_session.delete(route)
        self._db_session.commit()
