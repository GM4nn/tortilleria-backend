# fastapi
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# auth
from app.core.deps import (
    get_current_user,
    read_any_write_admin,
    require_admin,
    require_api_key,
)

# contextlib
from contextlib import asynccontextmanager

# config
from app.core.config import settings

# alembic
from alembic.config import Config
from alembic import command

# bootstrap (datos por defecto)
from app.core.bootstrap import run_bootstrap

# firestore + websocket
from app.src.services.firestore import firestore_service
from app.src.services.ws_manager import ws_manager
from app.src.routers import ws

# routers
from app.src.routers import (
    assistant,
    auth,
    cash_cut,
    customer,
    customer_price,
    dealer,
    meta,
    order,
    product,
    report,
    sale,
    supplier,
    supply,
    user,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    command.upgrade(Config("alembic.ini"), "head")
    run_bootstrap()
    ws_manager.set_loop(asyncio.get_running_loop())
    firestore_service.start_order_sync()
    yield

app = FastAPI(
    title="TORTILLERIA-API",
    description="API web del sistema de la tortilleria.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# Auth es público (login)
app.include_router(auth.router, prefix="/api")

# WebSocket de pedidos (valida el token por query param dentro del endpoint)
app.include_router(ws.router)

# Gestión de usuarios: protegida con API key (SECRET_KEY), no con sesión
app.include_router(user.router, prefix="/api", dependencies=[Depends(require_api_key)])

# Cualquier usuario autenticado (ventas, pedidos y caja)
_user_routers = [
    order,
    sale,
    cash_cut
]

for module in _user_routers:
    app.include_router(module.router, prefix="/api", dependencies=[Depends(get_current_user)])

# Lectura para cualquier autenticado (para armar ventas/pedidos); escritura solo admin
_read_routers = [
    product,
    customer,
    dealer,
]

for module in _read_routers:
    app.include_router(module.router, prefix="/api", dependencies=[Depends(read_any_write_admin)])

# Solo admin: precios personalizados, proveedores, insumos, reportes/finanzas,
# asistente y meta
_admin_routers = [
    customer_price,
    supplier,
    supply,
    report,
    assistant,
    meta,
]

for module in _admin_routers:
    app.include_router(module.router, prefix="/api", dependencies=[Depends(require_admin)])


@app.get(
    "/",
    tags=["Health"],
    description="Health check para comprobar que la api responda"
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "tortilleria-api"
    }
