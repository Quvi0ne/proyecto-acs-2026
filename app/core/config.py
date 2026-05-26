import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def _database_url() -> str:
    host = os.getenv("RDS_HOSTNAME")
    if host:
        port = os.getenv("RDS_PORT", "5432")
        name = os.getenv("RDS_DB_NAME", "ebdb")
        user = os.getenv("RDS_USERNAME", "")
        password = os.getenv("RDS_PASSWORD", "")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}?ssl=require"
    return os.getenv("DATABASE_URL", "")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = _database_url()
    JWT_SECRET: str = "change-me"
    JWT_EXPIRE_MINUTES: int = 30
    ADMIN_EMAIL: str = "admin@sece.local"
    ADMIN_PASSWORD: str = "Admin1234!"


settings = Settings()
