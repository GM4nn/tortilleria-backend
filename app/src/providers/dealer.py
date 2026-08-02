# sqlalchemy
from sqlalchemy.orm import Session

# schemas
from app.src.schemas.dealer import DealerCreate, DealerUpdate

# models
from app.src.models import Dealer, Order

# services
from app.src.services.firestore import firestore_service


class DealerProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_all(self) -> list[Dealer]:
        return self._db_session.query(Dealer)\
            .filter(Dealer.active.is_(True))\
            .order_by(Dealer.name)\
            .all()

    def get_by_username(self, username: str) -> Dealer | None:
        return self._db_session.query(Dealer).filter(
            Dealer.username == username
        ).first()

    def create(self, data: DealerCreate) -> Dealer:

        if self.get_by_username(data.username):
            raise ValueError("Ya existe un repartidor con ese usuario")

        dealer: Dealer = Dealer(
            username=data.username,
            pin=data.pin,
            name=data.name,
        )
        self._db_session.add(dealer)
        self._db_session.commit()
        self._db_session.refresh(dealer)

        firestore_service.upsert_dealer(dealer.username, dealer.pin, dealer.name)
        return dealer

    def update(self, dealer_id: int, data: DealerUpdate) -> Dealer:

        dealer: Dealer | None = self._db_session.query(Dealer).filter(
            Dealer.id == dealer_id
        ).first()

        if not dealer:
            raise ValueError("Repartidor no encontrado")

        existing: Dealer | None = self.get_by_username(data.username)
        if existing and existing.id != dealer_id:
            raise ValueError("Ya existe un repartidor con ese usuario")

        old_username: str = dealer.username
        dealer.username = data.username
        dealer.pin = data.pin
        dealer.name = data.name
        self._db_session.commit()
        self._db_session.refresh(dealer)

        if old_username != data.username:
            firestore_service.delete_dealer(old_username)
        firestore_service.upsert_dealer(dealer.username, dealer.pin, dealer.name)

        return dealer

    def delete(self, dealer_id: int) -> None:

        dealer: Dealer | None = self._db_session.query(Dealer).filter(
            Dealer.id == dealer_id
        ).first()

        if not dealer:
            raise ValueError("Repartidor no encontrado")

        username: str = dealer.username
        # Borrado real: los pedidos conservan su historial pero quedan sin repartidor
        self._db_session.query(Order).filter(Order.default_dealer == username).update(
            {Order.default_dealer: None}, synchronize_session=False
        )
        self._db_session.delete(dealer)
        self._db_session.commit()

        firestore_service.delete_dealer(username)
