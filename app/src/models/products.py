from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.core.base import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    icon = Column(String, default='🍴')
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    active = Column(Boolean, default=True)

    # Relationship
    # Al borrar un producto se borran los detalles de venta que lo referencian
    sales_details = relationship('SaleDetail', back_populates='product', cascade='all, delete')

    def __repr__(self):
        return f"<Product(id={self.id}, icon='{self.icon}', name='{self.name}', price={self.price})>"
