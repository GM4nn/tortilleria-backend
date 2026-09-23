"""Correr en producción con:
fly ssh console -c "python /code/sync_prod.py"
"""
import sys
sys.path.insert(0, '/code')

from app.core.database import SessionLocal
from app.src.models import Order, Customer
from app.src.services.firestore import firestore_service
from datetime import datetime, timedelta

db = SessionLocal()
today = datetime.now().date()
day_start = datetime(today.year, today.month, today.day)
day_end = day_start + timedelta(days=1)

orders = db.query(Order).filter(Order.date >= day_start, Order.date < day_end).all()
print(f'Ordenes en SQLite hoy: {len(orders)}')

synced = 0
errors = 0
for o in orders:
    c = db.query(Customer).filter(Customer.id == o.customer_id).first()
    if not c:
        print(f'  SKIP #{o.id}: customer {o.customer_id} no encontrado')
        errors += 1
        continue
    route = c.route
    fs_items = []
    for d in o.order_details:
        prod = d.product
        fs_items.append({
            "product_id": d.product_id,
            "name": prod.name if prod else "N/A",
            "price": d.unit_price,
            "quantity": d.quantity,
            "subtotal": d.subtotal,
            "grammage": d.grammage,
        })
    try:
        firestore_service.add_order(
            order_id=o.id,
            customer_name=c.customer_name,
            customer_id=c.id,
            items=fs_items,
            total=o.total,
            amount_paid=o.amount_paid or 0.0,
            created_at=o.date.isoformat() if o.date else "",
            default_dealer=o.default_dealer,
            notes=o.notes,
            customer_lat=c.latitude,
            customer_lng=c.longitude,
            customer_direction=c.customer_direction,
            route_id=c.route_id,
            route_name=route.name if route else None,
            route_color=route.color if route else None,
            route_dealers=route.dealer_usernames if route else [],
        )
        synced += 1
        print(f'  OK #{o.id} {c.customer_name}')
    except Exception as e:
        errors += 1
        print(f'  ERROR #{o.id}: {e}')

print(f'\nSincronizados: {synced}/{len(orders)}, errores: {errors}')
db.close()
