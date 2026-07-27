# datetime
from datetime import date

# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.sale import SaleProvider
from app.src.schemas.sale import PaginatedSales, SaleCreate, SaleRead


router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=PaginatedSales)
def list_sales(
    date_from: date | None = None,
    date_to: date | None = None,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    provider = SaleProvider(db)
    filters = provider.build_date_range_filter(date_from, date_to)
    return provider.get_all_paginated(offset=offset, limit=limit, filters=filters)


@router.get("/today")
def sales_today(db: Session = Depends(get_db)):
    return SaleProvider(db).get_today()


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    return SaleProvider(db).get_by_id(sale_id)


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(data: SaleCreate, db: Session = Depends(get_db)):
    return SaleProvider(db).create(data)
