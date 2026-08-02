from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.core.base import Base
from app.core.constants import mexico_now


class Sale(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=mexico_now)
    total = Column(Float, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)

    # Relationships
    sales_details = relationship('SaleDetail', back_populates='sale', cascade='all, delete-orphan')
    # Al borrar un cliente se borran sus ventas (y por cascada sus detalles)
    customer = relationship('Customer', backref=backref('sales', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Sale(id={self.id}, date={self.date}, total={self.total}, customer_id={self.customer_id})>"
