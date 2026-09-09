# pydantic
from pydantic import BaseModel, ConfigDict, Field


class RouteBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#ff4d6d", max_length=20)
    dealer_username: str | None = None


class RouteCreate(RouteBase):
    pass


class RouteUpdate(RouteBase):
    pass


class RouteRead(BaseModel):
    id: int
    name: str
    color: str | None
    dealer_username: str | None
    active: bool

    model_config = ConfigDict(from_attributes=True)
