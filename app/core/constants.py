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
CUSTOMER_CATEGORY_MOSTRADOR = "Mostrador"

# Listas desplegables (enums) — fuente única, sin tablas dedicadas
CUSTOMER_CATEGORIES = ["Mostrador", "Comedor", "Tienda"]

SUPPLY_UNITS = ["kilos", "litros", "piezas", "costales", "bultos", "cajas", "servicio"]

SUPPLIER_PRODUCT_TYPES = [
    "Maíz", "Harina", "Aceites", "Empaques", "Maquinaria", "Insumos Varios", "Otro",
]

# Tipo especial para proveedores del sistema (CFE, Gas Nieto). No va en el dropdown.
SUPPLIER_PRODUCT_TYPE_SERVICE = "Servicio"

PRODUCT_ICONS = [
    "🌮", "🥟", "📄", "🛍", "📐", "🍚", "🥜", "🍲", "🌶",
    "🍞", "🌯", "🥙", "🧀", "🌕", "🍴", "🥗", "🍳", "🥛",
    "🍯", "🌽", "🍋", "🥚", "🍪", "☕", "🥤", "🧂", "📦",
]
