# pydantic
from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=255)


class UserRead(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
