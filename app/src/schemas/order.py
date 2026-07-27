# datetime
from datetime import datetime

# pydantic
from pydantic import BaseModel, ConfigDict, Field

# app
from app.src.schemas.pagination import Pagination


class OrderItemInput(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_price: float = Field(gt=0)


class OrderCreate(BaseModel):
    customer_id: int
    notes: str | None = None
    amount_paid: float = Field(default=0.0, ge=0)
    default_dealer: str | None = None
    items: list[OrderItemInput] = Field(min_length=1)


class OrderDetailRead(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    subtotal: float


class OrderRead(BaseModel):
    id: int
    date: datetime | None
    total: float
    customer_id: int
    status: str
    completed_at: datetime | None
    notes: str | None
    amount_paid: float
    payment_status: str
    default_dealer: str | None
    details: list[OrderDetailRead] = []

    model_config = ConfigDict(from_attributes=True)


class PaymentInput(BaseModel):
    amount: float = Field(gt=0)


class RefundItemInput(BaseModel):
    product_id: int
    quantity: float = Field(ge=0)
    comments: str | None = None


class CompleteOrderInput(BaseModel):
    refund_items: list[RefundItemInput] = []
    final_payment: float = Field(default=0.0, ge=0)


class PaginatedOrders(BaseModel):
    pagination: Pagination
    data: list[OrderRead]
