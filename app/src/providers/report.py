# datetime
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now, ORDER_STATUSES_COMPLETE, ORDER_STATUSES_PENDING
from app.src.models import Customer, Order, Product, Sale, SaleDetail


class ReportProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def today_summary(self) -> dict:
        today = mexico_now().date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)

        sales = self._db_session.query(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.total), 0.0),
        ).filter(Sale.date >= day_start, Sale.date < day_end).first()

        orders = self._db_session.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0.0),
        ).filter(
            Order.status == ORDER_STATUSES_COMPLETE,
            Order.completed_at >= day_start,
            Order.completed_at < day_end,
        ).first()

        pending = self._db_session.query(func.count(Order.id)).filter(
            Order.status == ORDER_STATUSES_PENDING
        ).scalar() or 0

        return {
            "sales_count": sales[0] or 0,
            "sales_total": sales[1] or 0.0,
            "orders_completed_count": orders[0] or 0,
            "orders_completed_total": orders[1] or 0.0,
            "orders_pending_count": pending,
            "income_total": (sales[1] or 0.0) + (orders[1] or 0.0),
        }

    def top_products(self, limit: int = 5) -> list[dict]:
        rows = self._db_session.query(
            Product.name,
            func.coalesce(func.sum(SaleDetail.quantity), 0.0).label("qty"),
        ).join(SaleDetail, SaleDetail.product_id == Product.id)\
            .group_by(Product.id)\
            .order_by(func.sum(SaleDetail.quantity).desc())\
            .limit(limit).all()
        return [{"name": name, "quantity": qty or 0.0} for name, qty in rows]

    def top_customers(self, limit: int = 5) -> list[dict]:
        rows = self._db_session.query(
            Customer.customer_name,
            func.coalesce(func.sum(Sale.total), 0.0).label("total"),
        ).join(Sale, Sale.customer_id == Customer.id)\
            .group_by(Customer.id)\
            .order_by(func.sum(Sale.total).desc())\
            .limit(limit).all()
        return [{"customer_name": name, "total": total or 0.0} for name, total in rows]

    def monthly_income(self) -> dict:
        now = mexico_now()
        month_start = datetime(now.year, now.month, 1)

        sales_total = self._db_session.query(
            func.coalesce(func.sum(Sale.total), 0.0)
        ).filter(Sale.date >= month_start).scalar() or 0.0

        orders_total = self._db_session.query(
            func.coalesce(func.sum(Order.total), 0.0)
        ).filter(
            Order.status == ORDER_STATUSES_COMPLETE,
            Order.completed_at >= month_start,
        ).scalar() or 0.0

        return {
            "month": now.strftime("%Y-%m"),
            "sales_total": sales_total,
            "orders_total": orders_total,
            "income_total": sales_total + orders_total,
        }
