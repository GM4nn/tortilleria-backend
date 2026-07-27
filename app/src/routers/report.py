# fastapi
from fastapi import APIRouter, Depends

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.report import ReportProvider


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/today", description="Resumen de hoy (ventas, pedidos, ingresos)")
def today_summary(db: Session = Depends(get_db)):
    return ReportProvider(db).today_summary()


@router.get("/top-products", description="Productos más vendidos")
def top_products(limit: int = 5, db: Session = Depends(get_db)):
    return ReportProvider(db).top_products(limit)


@router.get("/top-customers", description="Clientes con más compras")
def top_customers(limit: int = 5, db: Session = Depends(get_db)):
    return ReportProvider(db).top_customers(limit)


@router.get("/monthly-income", description="Ingresos del mes actual")
def monthly_income(db: Session = Depends(get_db)):
    return ReportProvider(db).monthly_income()
