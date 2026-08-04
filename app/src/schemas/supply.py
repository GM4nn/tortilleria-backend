# datetime
from datetime import date, datetime

# pydantic
from pydantic import BaseModel, ConfigDict, Field

# app
from app.src.schemas.pagination import Pagination


class SupplyBase(BaseModel):
    supply_name: str = Field(min_length=1, max_length=100)
    supplier_id: int | None = None
    unit: str = Field(default="kilos", max_length=50)


class SupplyCreate(SupplyBase):
    pass


class SupplyUpdate(SupplyBase):
    pass


class SupplyRead(BaseModel):
    id: int
    supply_name: str
    supplier_id: int | None
    unit: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


class SupplyPurchaseCreate(BaseModel):
    supplier_id: int
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    unit_price: float = Field(ge=0)
    total_price: float = Field(ge=0)
    remaining: float = Field(default=0.0, ge=0)
    purchase_date: date | None = None
    notes: str | None = None


class SupplyPurchaseRead(BaseModel):
    id: int
    supply_id: int
    supplier_id: int
    purchase_date: date | None
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    remaining: float
    notes: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PaginatedSupplyPurchases(BaseModel):
    pagination: Pagination
    data: list[SupplyPurchaseRead]


class SupplyPeriodRead(BaseModel):
    from_date: date | None
    to_date: date | None
    compra: float
    sobrante: float
    disponible: float
    consumido: float
    restante: float
    pct: float


class PaginatedSupplyPeriods(BaseModel):
    pagination: Pagination
    data: list[SupplyPeriodRead]
    current: SupplyPeriodRead | None = None
    inventory: float = 0.0
