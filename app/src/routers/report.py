# fastapi
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now
from app.core.database import get_db
from app.src.providers.report import ReportProvider
from app.src.services.excel_export import build_sales_workbook

# std
from io import BytesIO


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/export", description="Descarga un Excel con ventas, pedidos y resumen")
def export_excel(db: Session = Depends(get_db)) -> StreamingResponse:
    content = build_sales_workbook(db)
    filename = f"reporte-ventas-{mexico_now().strftime('%Y-%m-%d')}.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/today", description="Resumen de hoy (ventas, pedidos, ingresos)")
def today_summary(db: Session = Depends(get_db)):
    return ReportProvider(db).today_summary()


@router.get("/losses-total", description="Pérdidas: total de tortilla devuelta")
def losses_total(db: Session = Depends(get_db)):
    return ReportProvider(db).losses_total()


@router.get("/top-customers", description="Clientes con más compras")
def top_customers(limit: int = 5, db: Session = Depends(get_db)):
    return ReportProvider(db).top_customers(limit)


@router.get("/monthly-income", description="Ingresos del mes actual")
def monthly_income(db: Session = Depends(get_db)):
    return ReportProvider(db).monthly_income()


@router.get("/orders-breakdown", description="Conteo de pedidos por estado de entrega y pago")
def orders_breakdown(db: Session = Depends(get_db)):
    return ReportProvider(db).orders_breakdown()


@router.get("/finance", description="Finanzas: ingresos, gastos y ganancia (semana y mes)")
def finance(db: Session = Depends(get_db)):
    return ReportProvider(db).finance()
