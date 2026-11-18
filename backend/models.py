"""Modelo de datos (docs/diseno.md, sección 3)."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

ROLES = ("solicitante", "atencion", "coordinacion")
TIPOS_SOLICITANTE = ("estudiante", "docente", "egresado", "externo")
PRIORIDADES = ("alta", "media", "baja")
ESTADOS = (
    "recibida",
    "en_evaluacion",
    "pendiente_informacion",
    "en_gestion",
    "finalizada",
    "rechazada",
    "cancelada",
)
TIPOS_EVENTO = (
    "creada",
    "evaluacion_iniciada",
    "informacion_solicitada",
    "informacion_recibida",
    "aceptada",
    "rechazada",
    "asignada",
    "reasignada",
    "prioridad_cambiada",
    "nota",
    "finalizada",
    "cancelada",
)
PROPOSITOS_ADJUNTO = ("solicitud", "informacion", "respuesta")


def ahora() -> datetime:
    """Fecha y hora actuales en UTC, sin zona horaria (así las guarda SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _lista(valores) -> str:
    return ", ".join(f"'{v}'" for v in valores)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(f"rol IN ({_lista(ROLES)})", name="ck_usuarios_rol"),
        CheckConstraint(
            f"tipo_solicitante IS NULL OR tipo_solicitante IN ({_lista(TIPOS_SOLICITANTE)})",
            name="ck_usuarios_tipo_solicitante",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    correo: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))
    tipo_solicitante: Mapped[str | None] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Servicio(Base):
    __tablename__ = "servicios"
    __table_args__ = (
        CheckConstraint(
            f"prioridad_defecto IN ({_lista(PRIORIDADES)})",
            name="ck_servicios_prioridad_defecto",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str] = mapped_column(Text, default="")
    requiere_adjunto: Mapped[bool] = mapped_column(Boolean, default=False)
    prioridad_defecto: Mapped[str] = mapped_column(String(10), default="media")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Solicitud(Base):
    __tablename__ = "solicitudes"
    __table_args__ = (
        CheckConstraint(f"estado IN ({_lista(ESTADOS)})", name="ck_solicitudes_estado"),
        CheckConstraint(
            f"prioridad IN ({_lista(PRIORIDADES)})", name="ck_solicitudes_prioridad"
        ),
        Index("ix_solicitudes_estado", "estado"),
        Index("ix_solicitudes_responsable_id", "responsable_id"),
        Index("ix_solicitudes_solicitante_id", "solicitante_id"),
        Index("ix_solicitudes_servicio_id", "servicio_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado: Mapped[str] = mapped_column(String(20), unique=True)
    solicitante_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    servicio_id: Mapped[int] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT")
    )
    asunto: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(25), default="recibida")
    prioridad: Mapped[str] = mapped_column(String(10), default="media")
    responsable_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    respuesta: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, default=ahora, onupdate=ahora
    )
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime)

    solicitante: Mapped["Usuario"] = relationship(foreign_keys=[solicitante_id])
    responsable: Mapped["Usuario | None"] = relationship(foreign_keys=[responsable_id])
    servicio: Mapped["Servicio"] = relationship()
    eventos: Mapped[list["Evento"]] = relationship(
        back_populates="solicitud", order_by="Evento.creado_en, Evento.id"
    )
    adjuntos: Mapped[list["Adjunto"]] = relationship(back_populates="solicitud")


class Evento(Base):
    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint(f"tipo IN ({_lista(TIPOS_EVENTO)})", name="ck_eventos_tipo"),
        Index("ix_eventos_solicitud_id", "solicitud_id"),
        Index("ix_eventos_creado_en", "creado_en"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="RESTRICT")
    )
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    tipo: Mapped[str] = mapped_column(String(30))
    estado_anterior: Mapped[str | None] = mapped_column(String(25))
    estado_nuevo: Mapped[str | None] = mapped_column(String(25))
    de_responsable_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    a_responsable_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    detalle: Mapped[str | None] = mapped_column(Text)
    visible_solicitante: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)

    solicitud: Mapped["Solicitud"] = relationship(back_populates="eventos")
    autor: Mapped["Usuario"] = relationship(foreign_keys=[autor_id])
    de_responsable: Mapped["Usuario | None"] = relationship(
        foreign_keys=[de_responsable_id]
    )
    a_responsable: Mapped["Usuario | None"] = relationship(
        foreign_keys=[a_responsable_id]
    )


class Adjunto(Base):
    __tablename__ = "adjuntos"
    __table_args__ = (
        CheckConstraint(
            f"proposito IN ({_lista(PROPOSITOS_ADJUNTO)})", name="ck_adjuntos_proposito"
        ),
        Index("ix_adjuntos_solicitud_id", "solicitud_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="RESTRICT")
    )
    subido_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    proposito: Mapped[str] = mapped_column(String(15))
    nombre_original: Mapped[str] = mapped_column(String(255))
    nombre_almacenado: Mapped[str] = mapped_column(String(255))
    tipo_mime: Mapped[str] = mapped_column(String(100))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)

    solicitud: Mapped["Solicitud"] = relationship(back_populates="adjuntos")
    subido_por: Mapped["Usuario"] = relationship(foreign_keys=[subido_por_id])
