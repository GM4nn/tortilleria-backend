# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.src.models import Customer, CustomerProductPrice, Product
from app.src.schemas.product import ProductCreate, ProductUpdate
from app.src.services.firestore import firestore_service


class ProductProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_all(self) -> list[Product]:
        return self._db_session.query(Product).order_by(
            Product.display_order, Product.name
        ).all()

    def get_by_id(self, product_id: int) -> Product:
        product = self._db_session.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Producto no encontrado")
        return product

    def create(self, data: ProductCreate) -> Product:
        next_order = (self._db_session.query(func.max(Product.display_order)).scalar() or 0) + 1
        product = Product(
            icon=data.icon,
            name=data.name,
            price=data.price,
            display_order=next_order,
        )
        self._db_session.add(product)
        self._db_session.commit()
        self._db_session.refresh(product)
        firestore_service.upsert_product(product)
        return product

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get_by_id(product_id)
        product.icon = data.icon
        product.name = data.name
        product.price = data.price
        self._db_session.commit()
        self._db_session.refresh(product)
        firestore_service.upsert_product(product)
        return product

    def update_all_customer_prices(self, product_id: int, price: float) -> dict:
        """Actualiza el precio de pedidos para TODOS los clientes y lo guarda en el producto."""
        product = self.get_by_id(product_id)

        # Guardar order_price en el producto
        product.order_price = price

        existing = self._db_session.query(CustomerProductPrice).filter(
            CustomerProductPrice.product_id == product_id
        ).all()
        customer_ids_with_price = {e.customer_id for e in existing}

        # NO tocar los que ya tienen precio custom, solo crear los que faltan
        customers = self._db_session.query(Customer).filter(
            Customer.active.is_(True),
            Customer.active2.is_(False),
        ).all()
        created = 0
        for c in customers:
            if c.id not in customer_ids_with_price:
                self._db_session.add(CustomerProductPrice(
                    customer_id=c.id,
                    product_id=product_id,
                    custom_price=price,
                ))
                created += 1

        self._db_session.commit()
        self._db_session.refresh(product)

        # Sincronizar producto y clientes a Firestore
        firestore_service.upsert_product(product)
        for c in customers:
            firestore_service.upsert_customer(c)

        total = len(existing) + created
        print(f"[Products] Precio de pedidos de \"{product.name}\" actualizado a ${price:.2f} para {total} clientes")
        return {"updated": len(existing), "created": created, "total": total}

    def delete(self, product_id: int) -> None:
        product = self.get_by_id(product_id)
        if product.is_default:
            raise ValueError("No se puede eliminar un producto del sistema")
        self._db_session.delete(product)
        self._db_session.commit()
        firestore_service.delete_product(product_id)
        return {"message": "Producto eliminado correctamente"}