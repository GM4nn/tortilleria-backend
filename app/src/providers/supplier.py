# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.constants import mexico_now
from app.src.models import Supplier
from app.src.schemas.supplier import SupplierCreate, SupplierUpdate


class SupplierProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_all(self) -> list[Supplier]:
        return self._db_session.query(Supplier).filter(
            Supplier.active.is_(True)
        ).order_by(Supplier.supplier_name).all()

    def get_by_id(self, supplier_id: int) -> Supplier:
        supplier = self._db_session.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.active.is_(True),
        ).first()
        if not supplier:
            raise ValueError("Proveedor no encontrado")
        return supplier

    def create(self, data: SupplierCreate) -> Supplier:
        supplier = Supplier(
            supplier_name=data.supplier_name,
            contact_name=data.contact_name,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            product_type=data.product_type,
            notes=data.notes,
        )
        self._db_session.add(supplier)
        self._db_session.commit()
        self._db_session.refresh(supplier)
        return supplier

    def update(self, supplier_id: int, data: SupplierUpdate) -> Supplier:
        supplier = self.get_by_id(supplier_id)
        supplier.supplier_name = data.supplier_name
        supplier.contact_name = data.contact_name
        supplier.phone = data.phone
        supplier.email = data.email
        supplier.address = data.address
        supplier.city = data.city
        supplier.product_type = data.product_type
        supplier.notes = data.notes
        supplier.updated_at = mexico_now()
        self._db_session.commit()
        self._db_session.refresh(supplier)
        return supplier

    def delete(self, supplier_id: int) -> None:
        # Borrado real: borra las compras que lo referencian y desvincula los insumos
        # (el proveedor es opcional en el insumo, así que el insumo se conserva)
        supplier = self.get_by_id(supplier_id)
        if supplier.is_default:
            raise ValueError("No se puede eliminar un proveedor del sistema")
        self._db_session.delete(supplier)
        self._db_session.commit()
