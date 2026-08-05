# other libs
import json

# app
from app.core.config import settings
from app.core.constants import ORDER_STATUSES_COMPLETE, ORDER_STATUSES_PENDING, mexico_now
from app.core.database import SessionLocal
from app.src.models import Order
from app.src.services.ws_manager import ws_manager

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
        default_dealer: str | None = None,
    ) -> None:
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).document(str(order_id)).set(
                {
                    "order_id": order_id,
                    "customer_name": customer_name,
                    "items": items,
                    "total": total,
                    "amount_paid": amount_paid,
                    "status": ORDER_STATUSES_PENDING,
                    "created_at": created_at,
                    "default_dealer": default_dealer,
                }
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error order #{order_id}: {exc}")

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

    # -------- listener Firestore -> SQLite --------

    def start_order_sync(self) -> None:
        # Escucha cambios de pedidos en Firestore (abonos/estado/repartidor desde
        # el móvil) y los refleja en la SQLite. Corre en un hilo en segundo plano.
        if not self._available:
            return
        try:
            self._db.collection(self._orders_collection).on_snapshot(
                self._on_orders_snapshot
            )
            print("[Firestore] Listener de pedidos activo")
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] No se pudo iniciar el listener: {exc}")

    def _on_orders_snapshot(self, _col_snapshot, changes, _read_time) -> None:
        # Sesión propia porque el callback corre en un hilo aparte
        db = SessionLocal()
        changed = False
        try:
            for change in changes:
                if change.type.name not in ("ADDED", "MODIFIED"):
                    continue

                data = change.document.to_dict() or {}
                order_id = data.get("order_id")

                if order_id is None:
                    continue

                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    continue

                updated = False

                amount_paid = data.get("amount_paid")
                if amount_paid is not None and order.amount_paid != amount_paid:
                    order.amount_paid = amount_paid
                    updated = True

                if data.get("default_dealer") != order.default_dealer:
                    order.default_dealer = data.get("default_dealer")
                    updated = True

                new_status = data.get("status")
                if new_status and new_status != order.status:
                    order.status = new_status
                    if new_status == ORDER_STATUSES_COMPLETE and not order.completed_at:
                        order.completed_at = mexico_now()
                    updated = True

                if updated:
                    db.commit()
                    changed = True
        except Exception as exc:  # noqa: BLE001
            print(f"[Firestore] Error sync -> SQLite: {exc}")
        finally:
            db.close()

        # Avisa al frontend (una sola vez por lote) que hubo cambios
        if changed:
            ws_manager.notify("orders")


firestore_service: FirestoreService = FirestoreService()
