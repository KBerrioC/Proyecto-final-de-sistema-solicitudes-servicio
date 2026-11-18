"""Configuración de la aplicación, leída de variables de entorno o del archivo .env."""
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 30
    upload_dir: str = "uploads"
    max_upload_mb: int = 5

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


try:
    configuracion = Configuracion()
except ValidationError as error:
    raise RuntimeError(
        "Falta una configuración obligatoria. Copia .env.example como .env y define "
        "SECRET_KEY con al menos 32 caracteres. Detalle: " + str(error)
    ) from None
