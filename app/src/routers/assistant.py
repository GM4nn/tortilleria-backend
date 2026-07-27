# fastapi
from fastapi import APIRouter, Depends

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.schemas.assistant import AssistantAnswer, AssistantQuery
from app.src.services.assistant import AssistantService


router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AssistantAnswer)
def ask(data: AssistantQuery, db: Session = Depends(get_db)):
    answer = AssistantService(db).ask(data.question)
    return AssistantAnswer(answer=answer)
