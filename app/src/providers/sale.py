# datetime
from datetime import date, datetime, timedelta

# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now
from app.src.models import Product, Sale, SaleDetail
from app.src.providers.pagination import PaginationProvider
from app.src.schemas.sale import PaginatedSales, SaleCreate


class SaleProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def _to_dict(self, sale: Sale) -> dict:
        return {
            "id": sale.id,
            "date": sale.date,
            "total": sale.total,
            "customer_id": sale.customer_id,
            "details": [
                {
                    "product_id": d.product_id,
                    "product_name": d.product.name if d.product else "N/A",
                    "quantity": d.quantity,
                    "unit_price": d.unit_price,
                    "subtotal": d.subtotal,
                }
                for d in sale.sales_details
            ],
        }

    def get_all(self, offset: int = 0, limit: int | None = None, filters=None) -> list[dict]:
        query = self._db_session.query(Sale)
        if filters:
            query = query.filter(*filters)
        query = query.order_by(Sale.date.desc())
        if limit is not None:
            query = query.offset(offset).limit(limit)
        return [self._to_dict(s) for s in query.all()]

    def build_date_range_filter(self, start_date: date | None = None, end_date: date | None = None):
        filters = []
        if start_date:
            filters.append(
                Sale.date >= datetime(start_date.year, start_date.month, start_date.day)
            )
        if end_date:
            end = datetime(end_date.year, end_date.month, end_date.day) + timedelta(days=1)
            filters.append(Sale.date < end)
        return filters

    def get_all_paginated(self, offset: int = 0, limit: int = 10, filters=None) -> PaginatedSales:
        pagination = PaginationProvider(self._db_session).get_pagination_data(
            Sale, offset, limit, filters
        )
        data = self.get_all(offset=offset, limit=limit, filters=filters)
        return PaginatedSales(pagination=pagination, data=data)

    def get_by_id(self, sale_id: int) -> dict:
        sale = self._db_session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError("Venta no encontrada")
        return self._to_dict(sale)

    def create(self, data: SaleCreate) -> dict:
        details: list[SaleDetail] = []
        total: float = 0.0

        for item in data.items:
            product = self._db_session.query(Product).filter(
                Product.id == item.product_id
            ).first()
            if not product:
                raise ValueError(f"Producto {item.product_id} no encontrado")
            subtotal = item.quantity * item.unit_price
            total += subtotal
            details.append(SaleDetail(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=subtotal,
            ))

        sale = Sale(total=total, customer_id=data.customer_id)
        sale.sales_details = details
        self._db_session.add(sale)
        self._db_session.commit()
        self._db_session.refresh(sale)
        return self._to_dict(sale)

    def get_today(self) -> dict:
        today = mexico_now().date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)
        result = self._db_session.query(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.total), 0.0),
        ).filter(Sale.date >= day_start, Sale.date < day_end).first()
        return {"count": result[0] or 0, "total": result[1] or 0.0}
