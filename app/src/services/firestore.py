# other libs
import json
import threading

# app
from app.core.config import settings
from app.core.constants import (
    ORDER_STATUSES_PENDING,
    SHOP_LAT,
    SHOP_LNG,
)
from app.src.models import Customer, Product, Route

# firebase
from firebase_admin import credentials, firestore
import firebase_admin

class FirestoreService:
    """Sincroniza datos hacia Firestore para la app móvil (repartidores y pedidos).

    Si no hay credenciales queda desactivado (no-op): nada se rompe.
    """

    def __init__(self) -> None:
        self._db = None
        self._dealers_collection: str = settings.DEALERS_COLLECTION
        self._orders_collection: str = settings.ORDERS_COLLECTION
        self._customers_collection: str = settings.CUSTOMERS_COLLECTION
        self._routes_collection: str = settings.ROUTES_COLLECTION
        self._products_collection: str = settings.PRODUCTS_COLLECTION
        self._available: bool = False
        self._initialize()

    def _initialize(self) -> None:
        # Se acepta el service account como JSON en texto plano (ideal para secrets)
        # o como ruta a un archivo. Si no hay ninguno, queda desactivado.
        if settings.FIREBASE_CREDENTIALS_JSON:
            cred_source = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        elif settings.FIREBASE_CREDENTIALS_PATH:
            cred_source = settings.FIREBASE_CREDENTIALS_PATH
        else:
            return

        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Certificate(cred_source))
            self._db = firestore.client()
            self._available = True
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Sincronizacion desactivada: {exc}")

    # -------- dealers --------

    def upsert_dealer(self, username: str, pin: str, name: str) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._dealers_collection).document(username).set(
                {"username": username, "pin": pin, "display_name": name}
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error dealer {username}: {exc}")

    def delete_dealer(self, username: str) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._dealers_collection).document(username).delete()
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error borrando dealer {username}: {exc}")

    # -------- orders --------

    def add_order(
        self,
        order_id: int,
        customer_name: str,
        items: list[dict],
        total: float,
        amount_paid: float,
        created_at: str,
        customer_id: int | None = None,
        default_dealer: str | None = None,
        notes: str | None = None,
        customer_lat: float | None = None,
        customer_lng: float | None = None,
        customer_direction: str | None = None,
        route_id: int | None = None,
        route_name: str | None = None,
        route_color: str | None = None,
        route_dealers: list[str] | None = None,
        delivery_time: str | None = None,
    ) -> None:
        if not self._available:
            return
        _error = [None]
        def _sync():
            try:
                self._db.collection(self._orders_collection).document(str(order_id)).set(
                    {
                        "order_id": order_id,
                        "customer_name": customer_name,
                        "customer_id": customer_id,
                        "items": items,
                        "total": total,
                        "amount_paid": amount_paid,
                        "status": ORDER_STATUSES_PENDING,
                        "created_at": created_at,
                        "default_dealer": default_dealer,
                        "notes": notes or "",
                        "customer_lat": customer_lat,
                        "customer_lng": customer_lng,
                        "customer_direction": customer_direction,
                        "route_id": route_id,
                        "route_name": route_name,
                        "route_color": route_color,
                        "route_dealers": route_dealers or [],
                        "delivery_time": delivery_time,
                        "shop_lat": SHOP_LAT,
                        "shop_lng": SHOP_LNG,
                    }
                )
            except Exception as exc:
                _error[0] = exc

        t = threading.Thread(target=_sync, daemon=True)
        t.start()
        t.join(timeout=10)
        if t.is_alive():
            print(f"[Firestore] Timeout order #{order_id} (>10s)")
        elif _error[0]:
            print(f"[Firestore] Error order #{order_id}: {_error[0]}")

    def sync_order_items(self, order_id: int, items: list[dict], total: float) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).document(
                str(order_id)
            ).update({"items": items, "total": total})
        except Exception as exc:
            print(f"[Firestore] Error items order #{order_id}: {exc}")

    def update_order_status(self, order_id: int, status: str) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).document(str(order_id)).update(
                {"status": status}
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error status order #{order_id}: {exc}")

    def sync_payment(self, order_id: int, amount_paid: float) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).document(str(order_id)).update(
                {"amount_paid": amount_paid}
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error pago order #{order_id}: {exc}")

    def sync_dealer(self, order_id: int, dealer: str | None) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).document(str(order_id)).update(
                {"default_dealer": dealer}
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error repartidor order #{order_id}: {exc}")

    def sync_route_dealers(self, order_id: int, dealers: list[str]) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).document(str(order_id)).update(
                {"route_dealers": dealers or []}
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error route_dealers order #{order_id}: {exc}")

    def clear_orders(self) -> None:
        """Borra TODAS las órdenes de Firestore (limpieza nocturna). La SQLite
        conserva el historial; el móvil lee solo las del día."""
        if not self._available:
            return
        try:
            col = self._db.collection(self._orders_collection)
            batch = self._db.batch()
            count = 0
            for doc in col.stream():
                batch.delete(doc.reference)
                count += 1
                if count % 400 == 0:
                    batch.commit()
                    batch = self._db.batch()
            batch.commit()
            print(f"[Firestore] Órdenes limpiadas: {count}")
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error limpiando órdenes: {exc}")

    def clear_stale_orders(self, keep_date_prefix: str) -> int:
        """Borra de Firestore las órdenes anteriores a keep_date_prefix
        (keep_date_prefix = 'YYYY-MM-DD'), dejando intactas las de esa fecha en adelante."""
        if not self._available:
            return 0
        removed = 0
        try:
            col = self._db.collection(self._orders_collection)
            batch = self._db.batch()
            n = 0
            for doc in col.stream():
                data = doc.to_dict() or {}
                created = str(data.get("created_at") or "")
                # Extraer la parte de fecha (YYYY-MM-DD) del created_at
                created_date = created[:10] if len(created) >= 10 else created
                if created_date < keep_date_prefix:
                    batch.delete(doc.reference)
                    removed += 1
                    n += 1
                    if n % 400 == 0:
                        batch.commit()
                        batch = self._db.batch()
            batch.commit()
            print(f"[Firestore] Órdenes obsoletas eliminadas: {removed}")
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error limpiando obsoletas: {exc}")
        return removed

    # -------- clientes / rutas (para el mapa del móvil) --------

    def _customer_doc(self, c: Customer) -> dict:
        route = c.route
        # Precios personalizados del cliente {product_id: precio} (claves string
        # porque Firestore no admite claves numéricas en un map).
        prices = {
            str(p.product_id): p.custom_price
            for p in getattr(c, "product_prices", [])
        }
        return {
            "id": c.id,
            "name": c.customer_name,
            "lat": c.latitude,
            "lng": c.longitude,
            "direction": c.customer_direction or "",
            "route_id": c.route_id,
            "route_name": route.name if route else None,
            "route_color": route.color if route else None,
            "route_dealers": route.dealer_usernames if route else [],
            "prices": prices,
            "active": bool(getattr(c, "active", True)),
            "shop_lat": SHOP_LAT,
            "shop_lng": SHOP_LNG,
        }

    def upsert_customer(self, customer: Customer) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._customers_collection).document(
                str(customer.id)
            ).set(self._customer_doc(customer))
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error cliente #{customer.id}: {exc}")

    def delete_customer(self, customer_id: int) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._customers_collection).document(
                str(customer_id)
            ).delete()
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error borrando cliente #{customer_id}: {exc}")

    def sync_all_customers(self, db) -> None:
        if not self._available:
            return
        try:
            customers = db.query(Customer).filter(Customer.active.is_(True)).all()
            col = self._db.collection(self._customers_collection)
            batch = self._db.batch()
            n = 0
            for c in customers:
                batch.set(col.document(str(c.id)), self._customer_doc(c))
                n += 1
                if n % 400 == 0:
                    batch.commit()
                    batch = self._db.batch()
            batch.commit()
            print(f"[Firestore] Clientes sincronizados: {len(customers)}")
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error sincronizando clientes: {exc}")

    def sync_route_customers(self, db, route_id: int) -> None:
        """Re-sincroniza los clientes de una ruta (cuando cambia nombre/color/
        repartidores de la ruta)."""
        if not self._available:
            return
        try:
            customers = db.query(Customer).filter(Customer.route_id == route_id).all()
            for c in customers:
                self.upsert_customer(c)
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error sincronizando clientes de ruta {route_id}: {exc}")

    def _route_doc(self, r: Route) -> dict:
        return {
            "id": r.id,
            "name": r.name,
            "color": r.color,
            "dealers": r.dealer_usernames,
            "active": bool(r.active),
        }

    def upsert_route(self, route: Route) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._routes_collection).document(str(route.id)).set(
                self._route_doc(route)
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error ruta #{route.id}: {exc}")

    def delete_route(self, route_id: int) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._routes_collection).document(
                str(route_id)
            ).delete()
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error borrando ruta #{route_id}: {exc}")

    def sync_all_routes(self, db) -> None:
        if not self._available:
            return
        try:
            routes = db.query(Route).filter(Route.active.is_(True)).all()
            col = self._db.collection(self._routes_collection)
            batch = self._db.batch()
            for r in routes:
                batch.set(col.document(str(r.id)), self._route_doc(r))
            batch.commit()
            print(f"[Firestore] Rutas sincronizadas: {len(routes)}")
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error sincronizando rutas: {exc}")

    # -------- productos (catálogo global para "Agregar producto") --------

    def _product_doc(self, p: Product) -> dict:
        return {
            "id": p.id,
            "name": p.name,
            "icon": p.icon,
            "price": p.order_price if p.order_price is not None else p.price,
            "active": bool(p.active),
            "is_default": bool(p.is_default),
        }

    def upsert_product(self, product: Product) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._products_collection).document(
                str(product.id)
            ).set(self._product_doc(product))
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error producto #{product.id}: {exc}")

    def delete_product(self, product_id: int) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._products_collection).document(
                str(product_id)
            ).delete()
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error borrando producto #{product_id}: {exc}")

    def sync_all_products(self, db) -> None:
        if not self._available:
            return
        try:
            products = db.query(Product).filter(Product.active.is_(True)).all()
            col = self._db.collection(self._products_collection)
            batch = self._db.batch()
            for p in products:
                batch.set(col.document(str(p.id)), self._product_doc(p))
            batch.commit()
            print(f"[Firestore] Productos sincronizados: {len(products)}")
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error sincronizando productos: {exc}")


firestore_service: FirestoreService = FirestoreService()
