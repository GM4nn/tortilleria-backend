# datetime
from datetime import datetime, timedelta

# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.core.constants import (
    mexico_now,
    ORDER_STATUSES_CANCEL,
    ORDER_STATUSES_COMPLETE,
    ORDER_STATUSES_PENDING,
    PRODUCT_CODE_TORTILLA_KILO,
)
from app.src.models import Customer, Order, OrderRefund, Product, Sale, SupplyPurchase


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

    def losses_total(self) -> dict:
        # Pérdidas del producto identificado por su código (la tortilla de kilo)
        product = self._db_session.query(Product).filter(
            Product.code == PRODUCT_CODE_TORTILLA_KILO
        ).first()

        if not product:
            return {"name": None, "icon": None, "price": 0.0, "today": 0.0, "month": 0.0, "total": 0.0}

        def summed(*filters) -> float:
            query = self._db_session.query(
                func.coalesce(func.sum(OrderRefund.quantity), 0.0)
            ).filter(OrderRefund.product_id == product.id, *filters)
            return query.scalar() or 0.0

        now = mexico_now()
        today = now.date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)
        month_start = datetime(now.year, now.month, 1)

        return {
            "name": product.name,
            "icon": product.icon,
            "price": product.price,
            "today": summed(OrderRefund.created_at >= day_start, OrderRefund.created_at < day_end),
            "month": summed(OrderRefund.created_at >= month_start),
            "total": summed(),
        }

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

        orders_count = self._db_session.query(func.count(Order.id)).filter(
            Order.date >= month_start
        ).scalar() or 0

        return {
            "month": now.strftime("%Y-%m"),
            "sales_total": sales_total,
            "orders_total": orders_total,
            "orders_count": orders_count,
            "income_total": sales_total + orders_total,
        }

    def _finance_for(self, dt_start: datetime, date_start) -> dict:
        # Ingresos: ventas de mostrador + pedidos completados y totalmente pagados
        sales_total = self._db_session.query(
            func.coalesce(func.sum(Sale.total), 0.0)
        ).filter(Sale.date >= dt_start).scalar() or 0.0

        paid = func.coalesce(Order.amount_paid, 0.0)
        orders_total = self._db_session.query(
            func.coalesce(func.sum(Order.total), 0.0)
        ).filter(
            Order.status == ORDER_STATUSES_COMPLETE,
            paid >= Order.total,
            Order.completed_at >= dt_start,
        ).scalar() or 0.0

        # Gastos: compras de insumos
        expenses = self._db_session.query(
            func.coalesce(func.sum(SupplyPurchase.total_price), 0.0)
        ).filter(SupplyPurchase.purchase_date >= date_start).scalar() or 0.0

        income = sales_total + orders_total
        net = income - expenses
        margin = (net / income * 100) if income > 0 else 0.0

        return {
            "sales_total": sales_total,
            "orders_total": orders_total,
            "income": income,
            "expenses": expenses,
            "net": net,
            "margin": margin,
        }

    def finance(self) -> dict:
        now = mexico_now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())  # lunes de esta semana
        month_start = today.replace(day=1)

        week_dt = datetime(week_start.year, week_start.month, week_start.day)
        month_dt = datetime(month_start.year, month_start.month, month_start.day)

        return {
            "week": self._finance_for(week_dt, week_start),
            "month": self._finance_for(month_dt, month_start),
        }

    def orders_breakdown(self) -> dict:
        # Conteo de pedidos por estado de entrega y de pago, con Hoy y Mes
        now = mexico_now()
        today = now.date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)
        month_start = datetime(now.year, now.month, 1)

        paid = func.coalesce(Order.amount_paid, 0.0)
        not_cancelled = Order.status != ORDER_STATUSES_CANCEL

        def count(*filters) -> int:
            return self._db_session.query(func.count(Order.id)).filter(*filters).scalar() or 0

        def period_counts(*base_filters) -> dict:
            return {
                "today": count(*base_filters, Order.date >= day_start, Order.date < day_end),
                "month": count(*base_filters, Order.date >= month_start),
            }

        return {
            "by_status": {
                "pendiente": period_counts(Order.status == ORDER_STATUSES_PENDING),
                "completado": period_counts(Order.status == ORDER_STATUSES_COMPLETE),
                "cancelado": period_counts(Order.status == ORDER_STATUSES_CANCEL),
            },
            "by_payment": {
                "unpaid": period_counts(not_cancelled, paid <= 0),
                "partial": period_counts(not_cancelled, paid > 0, paid < Order.total),
                "paid": period_counts(not_cancelled, paid >= Order.total),
            },
        }
