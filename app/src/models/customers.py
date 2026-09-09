from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.constants import mexico_now


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String, nullable=False)
    customer_direction = Column(String)
    customer_category = Column(String)
    customer_photo = Column(String)
    customer_phone = Column(String)
    # Ubicación para el mapa de rutas
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=True)
    created_at = Column(DateTime, default=mexico_now)
    updated_at = Column(DateTime, default=mexico_now, onupdate=mexico_now)
    active = Column(Boolean, default=True)
    active2 = Column(Boolean, default=True)

    route = relationship('Route', backref='customers')

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.customer_name}')>"
