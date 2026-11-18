"""Entradas y salidas de la API (Pydantic)."""
from datetime import datetime
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


class PersonaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ServicioResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class AdjuntoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_original: str
    proposito: str
    tipo_mime: str
    tamano_bytes: int


class SolicitudDetalle(BaseModel):
    id: int
    radicado: str
    servicio: ServicioResumen
    asunto: str
    descripcion: str
    estado: str
    prioridad: str
    solicitante: PersonaResumen
    responsable: PersonaResumen | None
    respuesta: str | None
    adjuntos: list[AdjuntoSalida]
    creado_en: datetime
    actualizado_en: datetime
    finalizado_en: datetime | None
    dias_pendientes: int | None
    dias_atencion: int | None


class SolicitudItem(BaseModel):
    """Fila del listado (EP-07). `solicitante` solo se incluye para el personal."""

    id: int
    radicado: str
    asunto: str
    servicio: ServicioResumen
    estado: str
    prioridad: str
    solicitante: PersonaResumen | None = None
    responsable: PersonaResumen | None
    creado_en: datetime
    dias_pendientes: int | None


class SolicitudLista(BaseModel):
    total: int
    items: list[SolicitudItem]


class AutorEvento(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    rol: str


class EventoSalida(BaseModel):
    """Evento del historial (EP-16). `visible_solicitante` solo se incluye para el personal."""

    id: int
    tipo: str
    autor: AutorEvento
    estado_anterior: str | None
    estado_nuevo: str | None
    detalle: str | None
    creado_en: datetime
    visible_solicitante: bool | None = None
