# fastapi
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


_routers = [
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

for module in _routers:
    app.include_router(module.router, prefix="/api")


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
