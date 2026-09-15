# std
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import ORDER_STATUSES_PENDING, mexico_now
from app.src.models import Customer, Order, Route, RouteDealer
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

        # Refresca en Firestore la lista de repartidores de la ruta en TODOS los
        # pedidos de hoy (no solo los reasignados), para la visibilidad en móvil.
        route = self._db_session.query(Route).filter(Route.id == route_id).first()
        dealers = route.dealer_usernames if route else []
        for order in orders:
            firestore_service.sync_route_dealers(order.id, dealers)

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

    @staticmethod
    def _clean_dealers(data) -> list[str]:
        """Lista de repartidores sin vacíos ni duplicados (respeta el orden).
        Cae a dealer_username si el multiselect vino vacío (compatibilidad)."""
        names = [d for d in (getattr(data, "dealers", None) or []) if d]
        if not names and data.dealer_username:
            names = [data.dealer_username]
        seen: set[str] = set()
        return [n for n in names if not (n in seen or seen.add(n))]

    @staticmethod
    def _auto_dealer(names: list[str]) -> str | None:
        """A quién se asignan los pedidos generados: si hay UN repartidor, a él;
        si hay varios (o ninguno), queda sin asignar y cualquiera de la ruta lo toma."""
        return names[0] if len(names) == 1 else None

    def _set_dealers(self, route: Route, names: list[str]) -> None:
        route.dealers_assoc = [RouteDealer(dealer_username=n) for n in names]
        route.dealer_username = names[0] if names else None

    def create(self, data: RouteCreate) -> Route:
        names = self._clean_dealers(data)
        route = Route(name=data.name, color=data.color)
        self._set_dealers(route, names)
        self._db_session.add(route)
        self._db_session.commit()
        self._db_session.refresh(route)
        firestore_service.upsert_route(route)
        return route

    def update(self, route_id: int, data: RouteUpdate) -> Route:
        route = self.get_by_id(route_id)
        old_auto = self._auto_dealer(route.dealer_usernames)
        names = self._clean_dealers(data)
        route.name = data.name
        route.color = data.color
        self._set_dealers(route, names)
        self._db_session.commit()
        # Propaga a los pedidos de hoy de la ruta (sin repartidor o con el viejo)
        self._reassign_todays_orders(route_id, self._auto_dealer(names), old_auto)
        self._db_session.refresh(route)
        # Refleja la ruta y sus clientes en el mapa del móvil
        firestore_service.upsert_route(route)
        firestore_service.sync_route_customers(self._db_session, route_id)
        return route

    def delete(self, route_id: int) -> None:
        route = self.get_by_id(route_id)
        # Clientes afectados (quedarán sin ruta) para re-sincronizarlos después
        affected = [
            cid
            for (cid,) in self._db_session.query(Customer.id)
            .filter(Customer.route_id == route_id)
            .all()
        ]
        # Los clientes de la ruta quedan sin ruta (no se borran)
        self._db_session.query(Customer).filter(Customer.route_id == route_id).update(
            {Customer.route_id: None}, synchronize_session=False
        )
        self._db_session.delete(route)
        self._db_session.commit()
        firestore_service.delete_route(route_id)
        for cid in affected:
            c = self._db_session.query(Customer).filter(Customer.id == cid).first()
            if c:
                firestore_service.upsert_customer(c)
