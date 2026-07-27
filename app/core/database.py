# other libs
from collections.abc import Generator

# sqlalchemy
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

# app
from app.core.config import settings


_connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URI.startswith("sqlite") else {}
)

engine: Engine = create_engine(
    settings.DATABASE_URI,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db() -> Generator[Session, None, None]:

    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
