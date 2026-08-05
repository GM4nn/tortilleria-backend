# pydantic settings
from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DATABASE_PATH: str = "tortilleria.db"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Firestore (sincronización con la app móvil)
    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_CREDENTIALS_JSON: str | None = None  # el service account como JSON en texto plano
    DEALERS_COLLECTION: str = "dealers"
    ORDERS_COLLECTION: str = "orders"

    # Asistente IA
    ANTHROPIC_API_KEY: str | None = None

    # Autenticación (JWT)
    SECRET_KEY: str = ""
    TOKEN_EXPIRE_DAYS: int = 30

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        # Ancla la BD a la carpeta backend/ sin importar el directorio actual
        root = Path(__file__).resolve().parents[2]
        path = Path(self.DATABASE_PATH)
        if not path.is_absolute():
            path = root / path
        return f"sqlite:///{path.as_posix()}"

    @computed_field
    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    _root: Path = Path(__file__).resolve().parents[2]
    model_config = {"env_file": [_root / ".env", _root / ".env.local"]}


settings: Settings = Settings()
