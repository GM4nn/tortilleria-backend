# fastapi
from fastapi import APIRouter, Depends

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.customer_price import CustomerPriceProvider
from app.src.schemas.customer_price import CustomerPriceRead, CustomerPriceSet


router = APIRouter(prefix="/customers", tags=["customer-prices"])


@router.get("/{customer_id}/prices", response_model=list[CustomerPriceRead])
def list_customer_prices(customer_id: int, db: Session = Depends(get_db)):
    return CustomerPriceProvider(db).get_for_customer(customer_id)


@router.put("/{customer_id}/prices", response_model=CustomerPriceRead)
def set_customer_price(customer_id: int, data: CustomerPriceSet, db: Session = Depends(get_db)):
    return CustomerPriceProvider(db).save_price(customer_id, data.product_id, data.price)
