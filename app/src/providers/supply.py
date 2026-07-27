# datetime
from datetime import date

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.src.models import Supply, SupplyPurchase
from app.src.schemas.supply import SupplyCreate, SupplyPurchaseCreate, SupplyUpdate


class SupplyProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_all(self) -> list[Supply]:
        return self._db_session.query(Supply).order_by(Supply.supply_name).all()

    def get_by_id(self, supply_id: int) -> Supply:
        supply = self._db_session.query(Supply).filter(Supply.id == supply_id).first()
        if not supply:
            raise ValueError("Insumo no encontrado")
        return supply

    def create(self, data: SupplyCreate) -> Supply:
        exists = self._db_session.query(Supply).filter(
            Supply.supply_name == data.supply_name
        ).first()
        if exists:
            raise ValueError("Ya existe un insumo con ese nombre")

        supply = Supply(
            supply_name=data.supply_name,
            supplier_id=data.supplier_id,
            unit=data.unit,
        )
        self._db_session.add(supply)
        self._db_session.commit()
        self._db_session.refresh(supply)
        return supply

    def update(self, supply_id: int, data: SupplyUpdate) -> Supply:
        supply = self.get_by_id(supply_id)
        supply.supply_name = data.supply_name
        supply.supplier_id = data.supplier_id
        supply.unit = data.unit
        self._db_session.commit()
        self._db_session.refresh(supply)
        return supply

    def delete(self, supply_id: int) -> None:
        supply = self.get_by_id(supply_id)
        if supply.is_default:
            raise ValueError("No se puede eliminar un insumo del sistema")
        self._db_session.delete(supply)
        self._db_session.commit()

    # -------- compras --------

    def get_purchases(self, supply_id: int) -> list[SupplyPurchase]:
        return self._db_session.query(SupplyPurchase).filter(
            SupplyPurchase.supply_id == supply_id
        ).order_by(SupplyPurchase.purchase_date.desc()).all()

    def add_purchase(self, supply_id: int, data: SupplyPurchaseCreate) -> SupplyPurchase:
        self.get_by_id(supply_id)  # valida que exista
        purchase = SupplyPurchase(
            supply_id=supply_id,
            supplier_id=data.supplier_id,
            purchase_date=data.purchase_date or date.today(),
            quantity=data.quantity,
            unit=data.unit,
            unit_price=data.unit_price,
            total_price=data.total_price,
            remaining=data.remaining,
            notes=data.notes,
        )
        self._db_session.add(purchase)
        self._db_session.commit()
        self._db_session.refresh(purchase)
        return purchase
