# sqlalchemy
from sqlalchemy.orm import Session

# app
from app.core.security import hash_password, verify_password
from app.src.models import User
from app.src.schemas.user import UserCreate


class UserProvider:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def get_all(self) -> list[User]:
        return self._db_session.query(User).order_by(User.username).all()

    def authenticate(self, username: str, password: str) -> User | None:
        user = self._db_session.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password):
            return user
        return None

    def create(self, data: UserCreate) -> User:
        exists = self._db_session.query(User).filter(
            User.username == data.username
        ).first()
        if exists:
            raise ValueError("Ya existe un usuario con ese nombre")

        user = User(username=data.username, password=hash_password(data.password))
        self._db_session.add(user)
        self._db_session.commit()
        self._db_session.refresh(user)
        return user

    def delete(self, user_id: int) -> None:
        user = self._db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuario no encontrado")
        if self._db_session.query(User).count() <= 1:
            raise ValueError("Debe existir al menos un usuario")
        self._db_session.delete(user)
        self._db_session.commit()
