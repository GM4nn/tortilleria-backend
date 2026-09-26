# pydantic
from pydantic import BaseModel, Field


class ScheduledOrderItemIO(BaseModel):
    weekday: int = Field(ge=0, le=6)   # 0=lunes ... 6=domingo
    product_id: int
    quantity: float = Field(gt=0)
    price: float | None = None  # Precio personalizado opcional (sincroniza a Firestore)


class ScheduledOrderCreate(BaseModel):
    customer_id: int
    delivery_time: str | None = None
    default_dealer: str | None = None
    active: bool = True
    items: list[ScheduledOrderItemIO] = Field(default_factory=list)


class ScheduledOrderUpdate(ScheduledOrderCreate):
    pass


class ScheduledOrderRead(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    delivery_time: str | None
    default_dealer: str | None
    active: bool
    items: list[ScheduledOrderItemIO]


class GenerateResult(BaseModel):
    created: int
    skipped: int
    errors: int
    weekday: int
