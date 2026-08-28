# fastapi
from fastapi import APIRouter, Depends

# pydantic
from pydantic import BaseModel

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.config import settings
from app.core.constants import (
    CUSTOMER_CATEGORIES,
    PRODUCT_ICONS,
    SUPPLIER_PRODUCT_TYPES,
    SUPPLY_UNITS,
)
from app.core.database import get_db
from app.src.models import IAConfig


router = APIRouter(prefix="/meta", tags=["meta"])


class AnthropicKeyInput(BaseModel):
    key: str


@router.get("", description="Listas desplegables (enums) del sistema")
def get_meta() -> dict:
    return {
        "customer_categories": CUSTOMER_CATEGORIES,
        "supply_units": SUPPLY_UNITS,
        "supplier_product_types": SUPPLIER_PRODUCT_TYPES,
        "product_icons": PRODUCT_ICONS,
    }


@router.get("/anthropic-key", description="Indica si la API key de Anthropic está configurada")
def get_anthropic_key(db: Session = Depends(get_db)) -> dict:
    row = db.query(IAConfig).order_by(IAConfig.id.desc()).first()
    configured = bool((row and row.api_key) or settings.ANTHROPIC_API_KEY)
    return {"configured": configured}


@router.put("/anthropic-key", description="Guarda la API key de Anthropic")
def set_anthropic_key(data: AnthropicKeyInput, db: Session = Depends(get_db)) -> dict:
    key = data.key.strip()
    row = db.query(IAConfig).order_by(IAConfig.id.desc()).first()
    if row:
        row.api_key = key
    else:
        db.add(IAConfig(api_key=key))
    db.commit()
    return {"configured": bool(key)}
