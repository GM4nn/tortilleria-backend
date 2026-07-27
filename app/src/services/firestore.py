# app
from app.core.config import settings
from app.core.constants import ORDER_STATUSES_PENDING


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
        if not settings.FIREBASE_CREDENTIALS_PATH:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                firebase_admin.initialize_app(
                    credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                )
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


firestore_service: FirestoreService = FirestoreService()
