"""Configuración de la aplicación, leída de variables de entorno o del archivo .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    upload_dir: str = "uploads"
    max_upload_mb: int = 5

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


configuracion = Configuracion()
