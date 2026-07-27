# pydantic
from pydantic import BaseModel, ConfigDict, Field


class DealerBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    pin: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)


class DealerCreate(DealerBase):
    pass


class DealerUpdate(DealerBase):
    pass


class DealerRead(BaseModel):
    id: int
    username: str
    pin: str
    name: str
    active: bool

    model_config = ConfigDict(from_attributes=True)
