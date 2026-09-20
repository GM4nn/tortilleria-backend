# fastapi
from fastapi import APIRouter, Depends

# sqlalchemy
from sqlalchemy.orm import Session

# pydantic
from pydantic import BaseModel

# app
from app.core.database import get_db
from app.src.providers.order import OrderProvider
from app.src.providers.scheduled_order import ScheduledOrderProvider


router = APIRouter(prefix="/mobile", tags=["mobile"])


class GenerateOrderInput(BaseModel):
    customer_id: int
    dealer: str | None = None  # repartidor que lo genera (para asignarlo)


class NotesInput(BaseModel):
    notes: str = ""


class PaymentInput(BaseModel):
    amount_paid: float


class DeliveryItemIn(BaseModel):
    product_id: int
    quantity: float = 0
    returned: float = 0
    price: float = 0
    grammage: float = 0


class DeliveryInput(BaseModel):
    items: list[DeliveryItemIn]
    total: float
    amount_paid: float
    complete: bool = True  # False = solo guardar info (sigue pendiente)


class CompleteAllInput(BaseModel):
    order_ids: list[int]


@router.post("/generate-order", description="Genera el pedido de HOY de un cliente")
def generate_order(data: GenerateOrderInput, db: Session = Depends(get_db)):
    return ScheduledOrderProvider(db).generate_for_customer(
        data.customer_id, data.dealer
    )


@router.post("/orders/{order_id}/notes", description="Guarda las notas del pedido")
def order_notes(order_id: int, data: NotesInput, db: Session = Depends(get_db)):
    return OrderProvider(db).set_notes(order_id, data.notes)


@router.post("/orders/{order_id}/payment", description="Fija el total pagado del pedido")
def order_payment(order_id: int, data: PaymentInput, db: Session = Depends(get_db)):
    return OrderProvider(db).set_amount_paid(order_id, data.amount_paid)


@router.post("/orders/{order_id}/complete", description="Guarda/cierra la entrega (kilos/pago)")
def order_complete(order_id: int, data: DeliveryInput, db: Session = Depends(get_db)):
    items = [i.model_dump() for i in data.items]
    return OrderProvider(db).apply_delivery(
        order_id, items, data.total, data.amount_paid, complete=data.complete
    )


@router.get("/pending-orders", description="Órdenes pendientes de entrega o pago parcial (semanas anteriores)")
def pending_orders(db: Session = Depends(get_db)):
    return OrderProvider(db).get_pending_delivery()


@router.post("/complete-all", description="Completa y paga todas las órdenes indicadas")
def complete_all(data: CompleteAllInput, db: Session = Depends(get_db)):
    return OrderProvider(db).complete_all(data.order_ids)
