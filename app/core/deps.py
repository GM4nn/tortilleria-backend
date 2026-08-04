"""Dependencias de autenticación (JWT)."""

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import USER_ADMIN
from app.core.database import get_db
from app.core.security import decode_access_token
from app.src.models import User

_bearer = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    # Protege endpoints administrativos (gestión de usuarios) con el SECRET_KEY
    if not api_key or api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado"
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado"
        )

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado"
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    # Solo el usuario admin puede acceder (además de estar autenticado)
    if user.username != USER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede acceder a esta sección",
        )
    return user


def read_any_write_admin(
    request: Request, user: User = Depends(get_current_user)
) -> User:
    # Cualquier autenticado puede LEER (GET); solo el admin puede crear/editar/borrar
    if request.method not in ("GET", "HEAD", "OPTIONS") and user.username != USER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede modificar esto",
        )
    return user
