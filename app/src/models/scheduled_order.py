from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.constants import mexico_now


class ScheduledOrder(Base):
    """Plantilla de pedido recurrente de un cliente (lunes a domingo)."""
    __tablename__ = 'scheduled_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    delivery_time = Column(String(5), nullable=True)   # "HH:MM"
    default_dealer = Column(String(100), ForeignKey('dealers.username'), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=mexico_now)

    customer = relationship('Customer')
    items = relationship(
        'ScheduledOrderItem',
        back_populates='scheduled_order',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f"<ScheduledOrder(id={self.id}, customer_id={self.customer_id})>"


class ScheduledOrderItem(Base):
    """Un producto/kilos para un día de la semana dentro de una plantilla.

    weekday: 0=lunes ... 6=domingo. Un día sin items = no hay entrega ese día.
    """
    __tablename__ = 'scheduled_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scheduled_order_id = Column(Integer, ForeignKey('scheduled_orders.id'), nullable=False)
    weekday = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False)

    scheduled_order = relationship('ScheduledOrder', back_populates='items')
    product = relationship('Product')

    def __repr__(self):
        return f"<ScheduledOrderItem(sched={self.scheduled_order_id}, wd={self.weekday}, product={self.product_id})>"
