# other libs
from collections.abc import Generator

# sqlalchemy
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# app
from app.core.config import settings


_is_sqlite = settings.DATABASE_URI.startswith("sqlite")

# timeout: si otro está escribiendo, espera en vez de fallar con "database is locked"
_connect_args = (
    {"check_same_thread": False, "timeout": 30} if _is_sqlite else {}
)

engine: Engine = create_engine(
    settings.DATABASE_URI,
    pool_pre_ping=True,
    connect_args=_connect_args,
)


if _is_sqlite:
    # WAL: permite lecturas concurrentes con una escritura; busy_timeout evita
    # "database is locked" cuando el listener y un request escriben casi a la vez.
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")
        cursor.close()
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
