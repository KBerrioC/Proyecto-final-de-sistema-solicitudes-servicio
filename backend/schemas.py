"""Entradas y salidas de la API (Pydantic)."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

TipoSolicitante = Literal["estudiante", "docente", "egresado", "externo"]


class RegistroEntrada(BaseModel):
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    correo: EmailStr
    password: str = Field(min_length=8, max_length=72)
    tipo_solicitante: TipoSolicitante

    @field_validator("password")
    @classmethod
    def password_cabe_en_bcrypt(cls, valor: str) -> str:
        # bcrypt solo admite 72 bytes; con tildes o símbolos, 72 caracteres pueden pasarse.
        if len(valor.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes")
        return valor


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    rol: str
    tipo_solicitante: str | None


class UsuarioResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    rol: str


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResumen


class ServicioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    requiere_adjunto: bool
    prioridad_defecto: str


class AtencionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
