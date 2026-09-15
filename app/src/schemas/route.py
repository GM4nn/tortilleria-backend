# pydantic
from pydantic import BaseModel, ConfigDict, Field


class RouteBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#ff4d6d", max_length=20)
    # Uno o varios repartidores. Se mantiene dealer_username por compatibilidad,
    # pero el frontend manda 'dealers' (multiselect).
    dealer_username: str | None = None
    dealers: list[str] = Field(default_factory=list)


class RouteCreate(RouteBase):
    pass


class RouteUpdate(RouteBase):
    pass


class RouteRead(BaseModel):
    id: int
    name: str
    color: str | None
    dealer_username: str | None
    dealers: list[str]
    active: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_route(cls, route) -> "RouteRead":
        return cls(
            id=route.id,
            name=route.name,
            color=route.color,
            dealer_username=route.dealer_username,
            dealers=route.dealer_usernames,
            active=route.active,
        )
