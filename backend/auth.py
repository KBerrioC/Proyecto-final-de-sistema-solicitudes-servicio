"""Contraseñas, tokens JWT y dependencias de autenticación y de rol (RNF-01, RF-03)."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import configuracion
from .database import get_db
from .models import Usuario

ALGORITMO = "HS256"
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


@lru_cache
def hash_ficticio() -> str:
    """Se compara contra este hash cuando el correo no existe, para que el tiempo de
    respuesta no revele qué correos están registrados."""
    return hash_password("contraseña-ficticia")


def crear_token(usuario: Usuario) -> str:
    vence = datetime.now(timezone.utc) + timedelta(
        minutes=configuracion.access_token_expire_minutes
    )
    datos = {"sub": str(usuario.id), "rol": usuario.rol, "exp": vence}
    return jwt.encode(datos, configuracion.secret_key, algorithm=ALGORITMO)


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas o sesión vencida",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_usuario_actual(
    token: str | None = Depends(esquema_oauth2), db: Session = Depends(get_db)
) -> Usuario:
    if token is None:
        raise _no_autenticado()
    try:
        datos = jwt.decode(token, configuracion.secret_key, algorithms=[ALGORITMO])
        usuario_id = int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _no_autenticado() from None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise _no_autenticado()
    return usuario


def requiere_rol(*roles: str):
    """Dependencia que deja pasar solo a los usuarios con alguno de los roles indicados."""

    def verificar(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para realizar esta operación",
            )
        return usuario

    return verificar
