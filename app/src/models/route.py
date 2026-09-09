from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.base import Base
from app.core.constants import mexico_now


class Route(Base):
    """Ruta/Zona: agrupa clientes cercanos y se asigna a un repartidor."""
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default="#ff4d6d")  # color del marcador en el mapa
    dealer_username = Column(String(100), ForeignKey('dealers.username'), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=mexico_now)

    def __repr__(self):
        return f"<Route(id={self.id}, name='{self.name}')>"
