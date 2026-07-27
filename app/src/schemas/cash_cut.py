# datetime
from datetime import datetime

# pydantic
from pydantic import BaseModel, ConfigDict

# app
from app.src.schemas.pagination import Pagination


class CashCutPeriodSummary(BaseModel):
    sales_count: int
    sales_total: float
    orders_count: int
    orders_total: float
    expected_total: float


class CashCutCreate(BaseModel):
    opened_at: datetime
    sales_count: int
    orders_count: int
    sales_total: float
    orders_total: float
    expected_total: float
    declared_cash: float = 0.0
    declared_card: float = 0.0
    declared_transfer: float = 0.0
    declared_total: float = 0.0
    difference: float = 0.0
    notes: str | None = None


class CashCutRead(BaseModel):
    id: int
    opened_at: datetime | None
    closed_at: datetime | None
    sales_count: int
    orders_count: int
    sales_total: float
    orders_total: float
    expected_total: float
    declared_cash: float
    declared_card: float
    declared_transfer: float
    declared_total: float
    difference: float
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


class PaginatedCashCuts(BaseModel):
    pagination: Pagination
    data: list[CashCutRead]
