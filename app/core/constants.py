# datetime
from datetime import datetime
from zoneinfo import ZoneInfo


MEXICO_TZ = ZoneInfo("America/Mexico_City")


def mexico_now() -> datetime:
    return datetime.now(MEXICO_TZ)


# ORDER STATUSES
ORDER_STATUSES_ALL = "todos"
ORDER_STATUSES_PENDING = "pendiente"
ORDER_STATUSES_COMPLETE = "completado"
ORDER_STATUSES_CANCEL = "cancelado"

# PAYMENT STATUSES
PAYMENT_STATUS_ALL = "todos"
PAYMENT_STATUS_UNPAID = "Sin Pagar"
PAYMENT_STATUS_PARTIAL = "Parcialmente Pagado"
PAYMENT_STATUS_PAID = "Pagado"

# CUSTOMERS
CUSTOMER_MOSTRADOR_NAME = "Cliente Mostrador"
