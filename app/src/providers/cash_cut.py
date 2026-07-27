# datetime
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now, ORDER_STATUSES_COMPLETE
from app.src.models import CashCut, Order, Sale
from app.src.schemas.cash_cut import CashCutCreate


def _day_range(d) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day)
    return start, start + timedelta(days=1)


class CashCutProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_current_period_summary(self) -> dict:
        day_start, day_end = _day_range(mexico_now().date())

        sales_result = self._db_session.query(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.total), 0.0),
        ).filter(Sale.date >= day_start, Sale.date < day_end).first()

        orders_result = self._db_session.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0.0),
        ).filter(
            Order.status == ORDER_STATUSES_COMPLETE,
            Order.completed_at >= day_start,
            Order.completed_at < day_end,
        ).first()

        sales_count = sales_result[0] or 0
        sales_total = sales_result[1] or 0.0
        orders_count = orders_result[0] or 0
        orders_total = orders_result[1] or 0.0

        return {
            "sales_count": sales_count,
            "sales_total": sales_total,
            "orders_count": orders_count,
            "orders_total": orders_total,
            "expected_total": sales_total + orders_total,
        }

    def get_all(self) -> list[CashCut]:
        return self._db_session.query(CashCut).order_by(CashCut.closed_at.desc()).all()

    def get_by_id(self, cut_id: int) -> CashCut:
        cut = self._db_session.query(CashCut).filter(CashCut.id == cut_id).first()
        if not cut:
            raise ValueError("Corte no encontrado")
        return cut

    def get_today_cut(self) -> CashCut | None:
        day_start, day_end = _day_range(mexico_now().date())
        return self._db_session.query(CashCut).filter(
            CashCut.closed_at >= day_start,
            CashCut.closed_at < day_end,
        ).first()

    def create(self, data: CashCutCreate) -> CashCut:
        cut = CashCut(
            opened_at=data.opened_at,
            closed_at=mexico_now(),
            sales_count=data.sales_count,
            orders_count=data.orders_count,
            sales_total=data.sales_total,
            orders_total=data.orders_total,
            expected_total=data.expected_total,
            declared_cash=data.declared_cash,
            declared_card=data.declared_card,
            declared_transfer=data.declared_transfer,
            declared_total=data.declared_total,
            difference=data.difference,
            notes=data.notes,
        )
        self._db_session.add(cut)
        self._db_session.commit()
        self._db_session.refresh(cut)
        return cut
