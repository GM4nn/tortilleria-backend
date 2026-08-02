# fastapi
from fastapi import APIRouter

# app
from app.core.constants import (
    CUSTOMER_CATEGORIES,
    PRODUCT_ICONS,
    SUPPLIER_PRODUCT_TYPES,
    SUPPLY_UNITS,
)


router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("", description="Listas desplegables (enums) del sistema")
def get_meta() -> dict:
    return {
        "customer_categories": CUSTOMER_CATEGORIES,
        "supply_units": SUPPLY_UNITS,
        "supplier_product_types": SUPPLIER_PRODUCT_TYPES,
        "product_icons": PRODUCT_ICONS,
    }
