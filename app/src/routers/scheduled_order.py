# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# db
from app.core.database import get_db

# schemas
from app.src.schemas.scheduled_order import (
    GenerateResult,
    ScheduledOrderCreate,
    ScheduledOrderRead,
    ScheduledOrderUpdate,
)

# providers
from app.src.providers.scheduled_order import ScheduledOrderProvider
from app.src.services.firestore import firestore_service


router = APIRouter(prefix="/scheduled-orders", tags=["scheduled-orders"])


@router.get("", response_model=list[ScheduledOrderRead], description="Plantillas de pedido programado")
def list_scheduled(db: Session = Depends(get_db)):
    return ScheduledOrderProvider(db).get_all()


@router.post(
    "",
    response_model=ScheduledOrderRead,
    status_code=status.HTTP_201_CREATED,
    description="Crear una plantilla de pedido programado",
)
def create_scheduled(data: ScheduledOrderCreate, db: Session = Depends(get_db)):
    return ScheduledOrderProvider(db).create(data)


@router.put(
    "/{scheduled_id}",
    response_model=ScheduledOrderRead,
    description="Actualizar una plantilla",
)
def update_scheduled(scheduled_id: int, data: ScheduledOrderUpdate, db: Session = Depends(get_db)):
    return ScheduledOrderProvider(db).update(scheduled_id, data)


@router.delete(
    "/{scheduled_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Eliminar una plantilla",
)
def delete_scheduled(scheduled_id: int, db: Session = Depends(get_db)):
    ScheduledOrderProvider(db).delete(scheduled_id)


@router.post(
    "/generate-today",
    response_model=GenerateResult,
    description="Genera los pedidos de hoy desde las plantillas (idempotente)",
)
def generate_today(db: Session = Depends(get_db)):
    return ScheduledOrderProvider(db).generate_todays_orders()


@router.post(
    "/sync-today",
    description="Re-sincroniza TODAS las órdenes de hoy a Firestore (batch). "
                "Útil si el mobile no muestra pedidos.",
)
def sync_today(db: Session = Depends(get_db)):
    return firestore_service.sync_today_orders(db)
