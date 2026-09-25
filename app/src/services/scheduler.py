"""Scheduler ligero (asyncio) para trabajos semanales.

Sin dependencias extra: encaja en la máquina siempre-encendida de Fly.
Dos jobs (cada martes):
  - 00:00: limpiar las órdenes en Firestore (el móvil arranca la semana
    en limpio; la SQLite conserva el historial).
  - 04:00: generar los pedidos de la semana desde las plantillas programadas.
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

_scheduler_tasks: set[asyncio.Task] | None = None


def _generate_job() -> None:
    db = SessionLocal()
    try:
        result = ScheduledOrderProvider(db).generate_todays_orders()
        print(f"[Scheduler] Pedidos generados: {result}")
    finally:
        db.close()


def _cleanup_job() -> None:
    """Borra de Firestore solo las órdenes de la semana pasada."""
    now = mexico_now()
    week_start = now.date() - __import__('datetime').timedelta(days=now.weekday())
    firestore_service.clear_stale_orders(week_start.isoformat())


async def _run_weekly_at(weekday: int, hour: int, minute: int, job, name: str) -> None:
    """Espera hasta la próxima ocurrencia del weekday (0=lunes..6=domingo)
    a la hora/minuto indicados, y luego ejecuta job periódicamente cada
    semana a esa hora."""
    while True:
        now = mexico_now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_until = weekday - now.weekday()
        if days_until < 0 or (days_until == 0 and target <= now):
            target += timedelta(days=7)
        await asyncio.sleep((target - now).total_seconds())
        try:
            await asyncio.to_thread(job)
        except Exception as exc:
            print(f"[Scheduler] Error en '{name}': {exc}")


async def _run_daily_at(hour: int, minute: int, job, name: str) -> None:
    while True:
        now = mexico_now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        try:
            await asyncio.to_thread(job)
        except Exception as exc:
            print(f"[Scheduler] Error en '{name}': {exc}")


def start() -> None:
    """Lanza los jobs: limpieza semanal (martes 00:00) y generación diaria (04:00).
    Si ya hay tareas activas, no crea duplicados."""
    global _scheduler_tasks
    if _scheduler_tasks and any(not t.done() for t in _scheduler_tasks):
        print("[Scheduler] Tasks ya activos, omitiendo start()")
        return
    _scheduler_tasks = set()
    _scheduler_tasks.add(asyncio.create_task(_run_weekly_at(1, 0, 0, _cleanup_job, "limpiar Firestore")))
    _scheduler_tasks.add(asyncio.create_task(_run_daily_at(4, 0, _generate_job, "generar pedidos")))
    print("[Scheduler] Jobs activos: limpieza semanal martes 00:00 + generación diaria 04:00")
