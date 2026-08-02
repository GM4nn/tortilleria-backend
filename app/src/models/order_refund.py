from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.core.base import Base
from app.core.constants import mexico_now


class OrderRefund(Base):
    __tablename__ = 'order_refunds'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    comments = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=mexico_now)

    # Relationships
    # Devoluciones: se borran con su pedido (owner) y con el producto referenciado
    order = relationship('Order', backref=backref('refunds', cascade='all, delete-orphan'))
    product = relationship('Product', backref=backref('order_refunds', cascade='all, delete'))

    def __repr__(self):
        return f"<OrderRefund(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, qty={self.quantity})>"
