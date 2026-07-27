# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.cash_cut import CashCutProvider
from app.src.schemas.cash_cut import CashCutCreate, CashCutPeriodSummary, CashCutRead


router = APIRouter(prefix="/cash", tags=["cash"])


@router.get("/summary", response_model=CashCutPeriodSummary)
def current_period_summary(db: Session = Depends(get_db)):
    return CashCutProvider(db).get_current_period_summary()


@router.get("/today", response_model=CashCutRead | None)
def today_cut(db: Session = Depends(get_db)):
    return CashCutProvider(db).get_today_cut()


@router.get("", response_model=list[CashCutRead])
def list_cuts(db: Session = Depends(get_db)):
    return CashCutProvider(db).get_all()


@router.get("/{cut_id}", response_model=CashCutRead)
def get_cut(cut_id: int, db: Session = Depends(get_db)):
    return CashCutProvider(db).get_by_id(cut_id)


@router.post("", response_model=CashCutRead, status_code=status.HTTP_201_CREATED)
def create_cut(data: CashCutCreate, db: Session = Depends(get_db)):
    return CashCutProvider(db).create(data)
