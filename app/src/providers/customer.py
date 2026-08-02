# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import CUSTOMER_CATEGORY_MOSTRADOR, mexico_now
from app.src.models import Customer
from app.src.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_all(self) -> list[Customer]:
        return self._db_session.query(Customer).filter(
            Customer.active.is_(True),
            Customer.active2.is_(True),
        ).order_by(Customer.customer_name).all()

    def get_mostrador(self) -> Customer:
        # El Mostrador vive oculto (active2=False); se busca por categoría, no por la lista
        customer = self._db_session.query(Customer).filter(
            Customer.customer_category == CUSTOMER_CATEGORY_MOSTRADOR,
            Customer.active.is_(True),
        ).first()
        if not customer:
            raise ValueError("Cliente Mostrador no encontrado")
        return customer

    def get_by_id(self, customer_id: int) -> Customer:
        customer = self._db_session.query(Customer).filter(
            Customer.id == customer_id,
            Customer.active.is_(True),
        ).first()
        if not customer:
            raise ValueError("Cliente no encontrado")
        return customer

    def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            customer_name=data.customer_name,
            customer_direction=data.customer_direction,
            customer_category=data.customer_category,
            customer_photo=data.customer_photo,
            customer_phone=data.customer_phone,
        )
        self._db_session.add(customer)
        self._db_session.commit()
        self._db_session.refresh(customer)
        return customer

    def update(self, customer_id: int, data: CustomerUpdate) -> Customer:
        customer = self.get_by_id(customer_id)
        customer.customer_name = data.customer_name
        customer.customer_direction = data.customer_direction
        customer.customer_category = data.customer_category
        customer.customer_photo = data.customer_photo
        customer.customer_phone = data.customer_phone
        customer.updated_at = mexico_now()
        self._db_session.commit()
        self._db_session.refresh(customer)
        return customer

    def delete(self, customer_id: int) -> None:
        # Borrado real: arrastra pedidos, ventas y precios personalizados (cascada ORM)
        customer = self.get_by_id(customer_id)
        self._db_session.delete(customer)
        self._db_session.commit()
