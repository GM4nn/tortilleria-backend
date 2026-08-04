# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.supply import SupplyProvider
from app.src.schemas.supply import (
    PaginatedSupplyPeriods,
    PaginatedSupplyPurchases,
    SupplyCreate,
    SupplyPurchaseCreate,
    SupplyPurchaseRead,
    SupplyRead,
    SupplyUpdate,
)


router = APIRouter(prefix="/supplies", tags=["supplies"])


@router.get("", response_model=list[SupplyRead])
def list_supplies(db: Session = Depends(get_db)):
    return SupplyProvider(db).get_all()


@router.get("/{supply_id}", response_model=SupplyRead)
def get_supply(supply_id: int, db: Session = Depends(get_db)):
    return SupplyProvider(db).get_by_id(supply_id)


@router.post("", response_model=SupplyRead, status_code=status.HTTP_201_CREATED)
def create_supply(data: SupplyCreate, db: Session = Depends(get_db)):
    return SupplyProvider(db).create(data)


@router.put("/{supply_id}", response_model=SupplyRead)
def update_supply(supply_id: int, data: SupplyUpdate, db: Session = Depends(get_db)):
    return SupplyProvider(db).update(supply_id, data)


@router.delete("/{supply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supply(supply_id: int, db: Session = Depends(get_db)):
    SupplyProvider(db).delete(supply_id)


@router.get("/{supply_id}/purchases", response_model=PaginatedSupplyPurchases)
def list_purchases(
    supply_id: int,
    offset: int = 0,
    limit: int = 6,
    db: Session = Depends(get_db),
):
    return SupplyProvider(db).get_purchases_paginated(supply_id, offset=offset, limit=limit)


@router.get("/{supply_id}/periods", response_model=PaginatedSupplyPeriods)
def list_periods(
    supply_id: int,
    offset: int = 0,
    limit: int = 6,
    db: Session = Depends(get_db),
):
    return SupplyProvider(db).get_periods_paginated(supply_id, offset=offset, limit=limit)


@router.get("/{supply_id}/reference-purchase", response_model=SupplyPurchaseRead | None)
def reference_purchase(
    supply_id: int,
    exclude: int | None = None,
    db: Session = Depends(get_db),
):
    return SupplyProvider(db).get_reference_purchase(supply_id, exclude_purchase_id=exclude)


@router.get("/{supply_id}/purchases/{purchase_id}", response_model=SupplyPurchaseRead)
def get_purchase(supply_id: int, purchase_id: int, db: Session = Depends(get_db)):
    return SupplyProvider(db).get_purchase(purchase_id)


@router.post(
    "/{supply_id}/purchases",
    response_model=SupplyPurchaseRead,
    status_code=status.HTTP_201_CREATED,
)
def add_purchase(supply_id: int, data: SupplyPurchaseCreate, db: Session = Depends(get_db)):
    return SupplyProvider(db).add_purchase(supply_id, data)


@router.put(
    "/{supply_id}/purchases/{purchase_id}",
    response_model=SupplyPurchaseRead,
)
def update_purchase(
    supply_id: int,
    purchase_id: int,
    data: SupplyPurchaseCreate,
    db: Session = Depends(get_db),
):
    return SupplyProvider(db).update_purchase(purchase_id, data)
