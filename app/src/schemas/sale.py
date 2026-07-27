# datetime
from datetime import datetime

# pydantic
from pydantic import BaseModel, ConfigDict, Field


class SaleItemInput(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_price: float = Field(gt=0)


class SaleCreate(BaseModel):
    customer_id: int
    items: list[SaleItemInput] = Field(min_length=1)


class SaleDetailRead(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    subtotal: float


class SaleRead(BaseModel):
    id: int
    date: datetime | None
    total: float
    customer_id: int
    details: list[SaleDetailRead] = []

    model_config = ConfigDict(from_attributes=True)
