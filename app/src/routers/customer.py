# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.customer import CustomerProvider
from app.src.schemas.customer import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    PaginatedCustomers,
)


router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return CustomerProvider(db).get_all()


@router.get("/paginated", response_model=PaginatedCustomers)
def list_customers_paginated(
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    return CustomerProvider(db).get_all_paginated(offset=offset, limit=limit)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return CustomerProvider(db).get_by_id(customer_id)


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return CustomerProvider(db).create(data)


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    return CustomerProvider(db).update(customer_id, data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    CustomerProvider(db).delete(customer_id)
