# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# db
from app.core.database import get_db

# schemas
from app.src.schemas.dealer import DealerCreate, DealerRead, DealerUpdate

# providers
from app.src.providers.dealer import DealerProvider


router = APIRouter(prefix="/dealers", tags=["dealers"])


@router.get("", response_model=list[DealerRead], description="Lista de repartidores activos")
def list_dealers(db: Session = Depends(get_db)):
    return DealerProvider(db).get_all()


@router.post(
    "",
    response_model=DealerRead,
    status_code=status.HTTP_201_CREATED,
    description="Crear un repartidor"
)
def create_dealer(data: DealerCreate, db: Session = Depends(get_db)):
    return DealerProvider(db).create(data)


@router.put("/{dealer_id}", response_model=DealerRead, description="Actualizar un repartidor")
def update_dealer(dealer_id: int, data: DealerUpdate, db: Session = Depends(get_db)):
    return DealerProvider(db).update(dealer_id, data)


@router.delete(
    "/{dealer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Eliminar (desactivar) un repartidor"
)
def delete_dealer(dealer_id: int, db: Session = Depends(get_db)):
    DealerProvider(db).delete(dealer_id)
