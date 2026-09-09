"""Scheduler ligero (asyncio) para trabajos diarios.

Sin dependencias extra: encaja en la máquina siempre-encendida de Fly.
Dos jobs:
  - 00:00 (medianoche): limpiar las órdenes en Firestore (el móvil arranca el día
    en limpio; la SQLite conserva el historial).
  - 05:00: generar los pedidos del día desde las plantillas programadas.
Horas en America/Mexico_City (mexico_now).
"""
# std
import asyncio
from datetime import timedelta

# app
from app.core.constants import mexico_now
from app.core.database import SessionLocal
from app.src.providers.scheduled_order import ScheduledOrderProvider
from app.src.services.firestore import firestore_service


def _generate_job() -> None:
    db = SessionLocal()
    try:
        result = ScheduledOrderProvider(db).generate_todays_orders()
        print(f"[Scheduler] Pedidos del día generados: {result}")
    finally:
        db.close()


def _cleanup_job() -> None:
    firestore_service.clear_orders()


async def _run_daily_at(hour: int, minute: int, job, name: str) -> None:
    while True:
        now = mexico_now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        try:
            # los jobs son síncronos (DB/Firestore); se corren en un hilo aparte
            await asyncio.to_thread(job)
        except Exception as exc:  # noqa: BLE001
            print(f"[Scheduler] Error en '{name}': {exc}")


def start() -> None:
    """Lanza los jobs diarios en el event loop actual (llamar desde el lifespan)."""
    asyncio.create_task(_run_daily_at(0, 0, _cleanup_job, "limpiar Firestore"))
    asyncio.create_task(_run_daily_at(5, 0, _generate_job, "generar pedidos"))
    print("[Scheduler] Jobs diarios activos (00:00 limpieza, 05:00 generación)")
