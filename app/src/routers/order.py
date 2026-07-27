# datetime
from datetime import date

# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.order import OrderProvider
from app.src.schemas.order import (
    CompleteOrderInput,
    OrderCreate,
    OrderRead,
    PaginatedOrders,
    PaymentInput,
)


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=PaginatedOrders)
def list_orders(
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    dealer: str | None = None,
    customer_id: int | None = None,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    provider = OrderProvider(db)

    filters = provider.build_date_range_filter(date_from, date_to)
    if status:
        filters += provider.build_status_filter(status)
    if payment_status:
        filters += provider.build_payment_status_filter(payment_status)
    if dealer:
        filters += provider.build_dealer_filter(dealer)
    if customer_id:
        filters += provider.build_customer_filter(customer_id)

    return provider.get_all_paginated(offset=offset, limit=limit, filters=filters)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return OrderProvider(db).get_by_id(order_id)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    return OrderProvider(db).create(data)


@router.post("/{order_id}/payment", response_model=OrderRead)
def register_payment(order_id: int, data: PaymentInput, db: Session = Depends(get_db)):
    return OrderProvider(db).register_payment(order_id, data.amount)


@router.post("/{order_id}/complete", response_model=OrderRead)
def complete_order(order_id: int, data: CompleteOrderInput, db: Session = Depends(get_db)):
    return OrderProvider(db).complete_order(order_id, data)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    return OrderProvider(db).cancel(order_id)
