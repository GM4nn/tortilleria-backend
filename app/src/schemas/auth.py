# pydantic
from pydantic import BaseModel, ConfigDict, Field


class LoginInput(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
