# fastapi
from fastapi import APIRouter, Depends, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.src.providers.user import UserProvider
from app.src.schemas.user import UserCreate, UserRead


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):  
    return UserProvider(db).get_all()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return UserProvider(db).create(data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    UserProvider(db).delete(user_id)
