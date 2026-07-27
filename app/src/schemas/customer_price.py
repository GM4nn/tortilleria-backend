# pydantic
from pydantic import BaseModel, ConfigDict, Field


class CustomerPriceRead(BaseModel):
    product_id: int
    custom_price: float

    model_config = ConfigDict(from_attributes=True)


class CustomerPriceSet(BaseModel):
    product_id: int
    price: float = Field(gt=0)
