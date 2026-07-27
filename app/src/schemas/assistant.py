# pydantic
from pydantic import BaseModel, Field


class AssistantQuery(BaseModel):
    question: str = Field(min_length=1)


class AssistantAnswer(BaseModel):
    answer: str
