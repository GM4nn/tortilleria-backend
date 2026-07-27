# pydantic
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    icon: str = Field(default="🍴", max_length=10)
    name: str = Field(min_length=1, max_length=255)
    price: float = Field(gt=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(BaseModel):
    id: int
    icon: str
    name: str
    price: float

    model_config = ConfigDict(from_attributes=True)
