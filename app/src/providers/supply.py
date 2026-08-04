# other libs
from math import ceil

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now
from app.src.models import Supply, SupplyPurchase
from app.src.providers.pagination import PaginationProvider
from app.src.schemas.pagination import Pagination
from app.src.schemas.supply import (
    PaginatedSupplyPeriods,
    PaginatedSupplyPurchases,
    SupplyCreate,
    SupplyPurchaseCreate,
    SupplyUpdate,
)


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

    def _purchases_desc_query(self, supply_id: int):
        # Más recientes primero (fecha y luego id para desempatar)
        return (
            self._db_session.query(SupplyPurchase)
            .filter(SupplyPurchase.supply_id == supply_id)
            .order_by(SupplyPurchase.purchase_date.desc(), SupplyPurchase.id.desc())
        )

    def get_purchases(self, supply_id: int) -> list[SupplyPurchase]:
        return self._purchases_desc_query(supply_id).all()

    def get_purchases_paginated(
        self, supply_id: int, offset: int = 0, limit: int = 10
    ) -> PaginatedSupplyPurchases:
        pagination = PaginationProvider(self._db_session).get_pagination_data(
            SupplyPurchase, offset, limit, [SupplyPurchase.supply_id == supply_id]
        )
        data = self._purchases_desc_query(supply_id).offset(offset).limit(limit).all()
        return PaginatedSupplyPurchases(pagination=pagination, data=data)

    def get_purchase(self, purchase_id: int) -> SupplyPurchase:
        purchase = self._db_session.query(SupplyPurchase).filter(
            SupplyPurchase.id == purchase_id
        ).first()
        if not purchase:
            raise ValueError("Compra no encontrada")
        return purchase

    def get_reference_purchase(
        self, supply_id: int, exclude_purchase_id: int | None = None
    ) -> SupplyPurchase | None:
        # La compra del "periodo anterior": la más reciente (o la anterior a la editada)
        query = self._purchases_desc_query(supply_id)
        if exclude_purchase_id is not None:
            edited = self.get_purchase(exclude_purchase_id)
            query = query.filter(
                (SupplyPurchase.purchase_date < edited.purchase_date)
                | (
                    (SupplyPurchase.purchase_date == edited.purchase_date)
                    & (SupplyPurchase.id < edited.id)
                )
            )
        return query.first()

    @staticmethod
    def _period(older: SupplyPurchase, newer: SupplyPurchase) -> dict:
        compra = older.quantity
        sobrante = older.remaining or 0.0
        disponible = sobrante + compra
        restante = newer.remaining or 0.0
        consumido = disponible - restante
        return {
            "from_date": older.purchase_date,
            "to_date": newer.purchase_date,
            "compra": compra,
            "sobrante": sobrante,
            "disponible": disponible,
            "consumido": consumido,
            "restante": restante,
            "pct": (consumido / disponible * 100) if disponible > 0 else 0.0,
        }

    def get_periods_paginated(
        self, supply_id: int, offset: int = 0, limit: int = 10
    ) -> PaginatedSupplyPeriods:
        base = self._purchases_desc_query(supply_id)
        total_purchases = base.count()
        total_periods = max(0, total_purchases - 1)

        # Trae limit+1 compras desde el offset para armar los pares consecutivos
        rows = base.offset(offset).limit(limit + 1).all()
        data = [self._period(rows[i + 1], rows[i]) for i in range(len(rows) - 1)]

        per_page = limit or 1
        total_pages = ceil(total_periods / per_page) or 1
        current_page = (offset // per_page) + 1
        pagination = Pagination(
            total_data=total_periods,
            total_pages=total_pages,
            current_page=current_page,
            next_page=current_page + 1,
            prev_page=current_page - 1,
            last_page=total_pages,
        )

        # Resumen: período actual (los 2 más recientes) e inventario (última compra)
        latest = base.limit(2).all()
        current = self._period(latest[1], latest[0]) if len(latest) >= 2 else None
        inventory = (
            (latest[0].remaining or 0.0) + latest[0].quantity if latest else 0.0
        )

        return PaginatedSupplyPeriods(
            pagination=pagination, data=data, current=current, inventory=inventory
        )

    def add_purchase(self, supply_id: int, data: SupplyPurchaseCreate) -> SupplyPurchase:
        self.get_by_id(supply_id)  # valida que exista
        purchase = SupplyPurchase(
            supply_id=supply_id,
            supplier_id=data.supplier_id,
            purchase_date=data.purchase_date or mexico_now().date(),
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

    def update_purchase(self, purchase_id: int, data: SupplyPurchaseCreate) -> SupplyPurchase:
        purchase = self._db_session.query(SupplyPurchase).filter(
            SupplyPurchase.id == purchase_id
        ).first()
        if not purchase:
            raise ValueError("Compra no encontrada")

        purchase.supplier_id = data.supplier_id
        purchase.purchase_date = data.purchase_date or purchase.purchase_date
        purchase.quantity = data.quantity
        purchase.unit = data.unit
        purchase.unit_price = data.unit_price
        purchase.total_price = data.total_price
        purchase.remaining = data.remaining
        purchase.notes = data.notes
        self._db_session.commit()
        self._db_session.refresh(purchase)
        return purchase
