from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    JWT_SECRET: str = "change-me"
    JWT_EXPIRE_MINUTES: int = 30
    ADMIN_EMAIL: str = "admin@sece.local"
    ADMIN_PASSWORD: str = "Admin1234!"
    # Orígenes (dominios) del frontend que pueden llamar a la API, separados por coma
    CORS_ORIGINS: str = "http://localhost:5173"


settings = Settings()
