from sqlalchemy import Column, Integer, String, DateTime
from app.core.base import Base
from app.core.constants import mexico_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # hash PBKDF2
    created_at = Column(DateTime, default=mexico_now)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
