# sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

# app
from app.src.models import Product
from app.src.schemas.product import ProductCreate, ProductUpdate


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
        # El orden se asigna solo: el nuevo producto va al final
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
        return product

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get_by_id(product_id)
        product.icon = data.icon
        product.name = data.name
        product.price = data.price
        self._db_session.commit()
        self._db_session.refresh(product)
        return product

    def delete(self, product_id: int) -> None:
        product = self.get_by_id(product_id)
        if product.is_default:
            raise ValueError("No se puede eliminar un producto del sistema")
        self._db_session.delete(product)
        self._db_session.commit()
        return {"message": "Producto eliminado correctamente"}