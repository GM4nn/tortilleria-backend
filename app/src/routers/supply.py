# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.supply import SupplyProvider
from app.src.schemas.supply import (
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


@router.get("/{supply_id}/purchases", response_model=list[SupplyPurchaseRead])
def list_purchases(supply_id: int, db: Session = Depends(get_db)):
    return SupplyProvider(db).get_purchases(supply_id)


@router.post(
    "/{supply_id}/purchases",
    response_model=SupplyPurchaseRead,
    status_code=status.HTTP_201_CREATED,
)
def add_purchase(supply_id: int, data: SupplyPurchaseCreate, db: Session = Depends(get_db)):
    return SupplyProvider(db).add_purchase(supply_id, data)
