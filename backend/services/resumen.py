"""Resumen consolidado para coordinación (EP-18, RF-18, RN-10)."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ESTADOS, Servicio, Solicitud, Usuario, ahora
from ..schemas import (
    ConteoResponsable,
    ConteoServicio,
    PendienteAntigua,
    ResumenSalida,
)
from .solicitudes import ESTADOS_FINALES


def generar_resumen(db: Session, desde: date | None, hasta: date | None) -> ResumenSalida:
    filtros = []
    if desde:
        filtros.append(Solicitud.creado_en >= datetime.combine(desde, time.min))
    if hasta:
        filtros.append(Solicitud.creado_en < datetime.combine(hasta + timedelta(days=1), time.min))

    por_estado = {estado: 0 for estado in ESTADOS}
    for estado, total in db.execute(
        select(Solicitud.estado, func.count()).where(*filtros).group_by(Solicitud.estado)
    ):
        por_estado[estado] = total

    por_servicio = [
        ConteoServicio(servicio=nombre, total=total)
        for nombre, total in db.execute(
            select(Servicio.nombre, func.count(Solicitud.id))
            .join(Solicitud, Solicitud.servicio_id == Servicio.id)
            .where(*filtros)
            .group_by(Servicio.id)
            .order_by(func.count(Solicitud.id).desc(), Servicio.nombre)
        )
    ]
    por_responsable = [
        ConteoResponsable(responsable=nombre, total=total)
        for nombre, total in db.execute(
            select(Usuario.nombre, func.count(Solicitud.id))
            .join(Solicitud, Solicitud.responsable_id == Usuario.id)
            .where(*filtros)
            .group_by(Usuario.id)
            .order_by(func.count(Solicitud.id).desc(), Usuario.nombre)
        )
    ]

    finalizadas = db.execute(
        select(Solicitud.creado_en, Solicitud.finalizado_en).where(
            *filtros, Solicitud.estado == "finalizada", Solicitud.finalizado_en.is_not(None)
        )
    ).all()
    promedio = (
        round(sum((f - c).total_seconds() for c, f in finalizadas) / len(finalizadas) / 86400, 1)
        if finalizadas
        else None
    )

    antiguas = db.scalars(
        select(Solicitud)
        .where(*filtros, Solicitud.estado.not_in(ESTADOS_FINALES))
        .order_by(Solicitud.creado_en, Solicitud.id)
        .limit(10)
    ).all()
    ahora_utc = ahora()
    return ResumenSalida(
        total=sum(por_estado.values()),
        por_estado=por_estado,
        por_servicio=por_servicio,
        por_responsable=por_responsable,
        tiempo_promedio_atencion_dias=promedio,
        pendientes_mas_antiguas=[
            PendienteAntigua(
                id=s.id,
                radicado=s.radicado,
                asunto=s.asunto,
                estado=s.estado,
                responsable=s.responsable.nombre if s.responsable else None,
                dias_pendientes=(ahora_utc - s.creado_en).days,
            )
            for s in antiguas
        ],
    )
