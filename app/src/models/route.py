from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base
from app.core.constants import mexico_now


class Route(Base):
    """Ruta/Zona: agrupa clientes cercanos y se asigna a uno o varios repartidores."""
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default="#ff4d6d")  # color del marcador en el mapa
    # Repartidor "principal" (compatibilidad); la lista completa vive en route_dealers
    dealer_username = Column(String(100), ForeignKey('dealers.username'), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=mexico_now)

    # Varios repartidores por ruta
    dealers_assoc = relationship(
        'RouteDealer', cascade='all, delete-orphan', backref='route'
    )

    @property
    def dealer_usernames(self) -> list[str]:
        """Todos los repartidores de la ruta (incluye el principal aunque no esté
        en la tabla, por si viene de datos viejos)."""
        names = [d.dealer_username for d in self.dealers_assoc]
        if self.dealer_username and self.dealer_username not in names:
            names.insert(0, self.dealer_username)
        return names

    def __repr__(self):
        return f"<Route(id={self.id}, name='{self.name}')>"


class RouteDealer(Base):
    """Asociación ruta ↔ repartidor (una ruta puede tener varios repartidores)."""
    __tablename__ = 'route_dealers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey('routes.id'), nullable=False)
    dealer_username = Column(String(100), ForeignKey('dealers.username'), nullable=False)
