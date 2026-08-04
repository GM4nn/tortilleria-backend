# fastapi
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# auth
from app.core.deps import get_current_user, require_api_key

# contextlib
from contextlib import asynccontextmanager

# config
from app.core.config import settings

# alembic
from alembic.config import Config
from alembic import command

# bootstrap (datos por defecto)
from app.core.bootstrap import run_bootstrap

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
    command.upgrade(Config("alembic.ini"), "head")
    run_bootstrap()
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

# Gestión de usuarios: protegida con API key (SECRET_KEY), no con sesión
app.include_router(user.router, prefix="/api", dependencies=[Depends(require_api_key)])

# El resto del API exige token JWT
_protected_routers = [
    dealer,
    customer,
    customer_price,
    product,
    supplier,
    order,
    sale,
    cash_cut,
    supply,
    report,
    assistant,
    meta,
]

for module in _protected_routers:
    app.include_router(module.router, prefix="/api", dependencies=[Depends(get_current_user)])


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
