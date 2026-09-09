# pydantic
from pydantic import BaseModel, ConfigDict, Field

# app
from app.src.schemas.pagination import Pagination


class CustomerBase(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    customer_direction: str | None = None
    customer_category: str | None = None
    customer_photo: str | None = None
    customer_phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    route_id: int | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerRead(BaseModel):
    id: int
    customer_name: str
    customer_direction: str | None
    customer_category: str | None
    customer_photo: str | None
    customer_phone: str | None
    latitude: float | None
    longitude: float | None
    route_id: int | None

    model_config = ConfigDict(from_attributes=True)


class PaginatedCustomers(BaseModel):
    pagination: Pagination
    data: list[CustomerRead]
