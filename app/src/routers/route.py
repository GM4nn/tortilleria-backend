# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# db
from app.core.database import get_db

# schemas
from app.src.schemas.route import RouteCreate, RouteRead, RouteUpdate

# providers
from app.src.providers.route import RouteProvider


router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteRead], description="Lista de rutas/zonas activas")
def list_routes(db: Session = Depends(get_db)):
    return RouteProvider(db).get_all()


@router.post(
    "",
    response_model=RouteRead,
    status_code=status.HTTP_201_CREATED,
    description="Crear una ruta/zona",
)
def create_route(data: RouteCreate, db: Session = Depends(get_db)):
    return RouteProvider(db).create(data)


@router.put("/{route_id}", response_model=RouteRead, description="Actualizar una ruta/zona")
def update_route(route_id: int, data: RouteUpdate, db: Session = Depends(get_db)):
    return RouteProvider(db).update(route_id, data)


@router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Eliminar una ruta/zona",
)
def delete_route(route_id: int, db: Session = Depends(get_db)):
    RouteProvider(db).delete(route_id)
