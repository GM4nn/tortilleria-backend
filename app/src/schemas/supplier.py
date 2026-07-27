# pydantic
from pydantic import BaseModel, ConfigDict, Field


class SupplierBase(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=100)
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    product_type: str | None = None
    notes: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    pass


class SupplierRead(BaseModel):
    id: int
    supplier_name: str
    contact_name: str | None
    phone: str | None
    email: str | None
    address: str | None
    city: str | None
    product_type: str | None
    notes: str | None
    is_default: bool

    model_config = ConfigDict(from_attributes=True)
