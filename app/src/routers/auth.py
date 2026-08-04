# fastapi
from fastapi import APIRouter, Depends, HTTPException, status

# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.src.models import User
from app.src.providers.user import UserProvider
from app.src.schemas.auth import LoginInput, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("", response_model=TokenResponse)
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = UserProvider(db).authenticate(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)