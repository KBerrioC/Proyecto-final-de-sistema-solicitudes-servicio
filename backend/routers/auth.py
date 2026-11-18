"""EP-01 a EP-03: registro, inicio de sesión y perfil."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import (
    crear_token,
    get_usuario_actual,
    hash_ficticio,
    hash_password,
    verificar_password,
)
from ..database import get_db
from ..models import Usuario
from ..schemas import RegistroEntrada, TokenSalida, UsuarioSalida

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/registro", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED)
def registrar(datos: RegistroEntrada, db: Session = Depends(get_db)):
    """EP-01: crea una cuenta de solicitante."""
    correo = datos.correo.lower()
    if db.scalar(select(Usuario).where(Usuario.correo == correo)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo")
    usuario = Usuario(
        nombre=datos.nombre,
        correo=correo,
        password_hash=hash_password(datos.password),
        rol="solicitante",
        tipo_solicitante=datos.tipo_solicitante,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo"
        ) from None
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenSalida)
def iniciar_sesion(
    formulario: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """EP-02: inicia sesión. `username` es el correo."""
    usuario = db.scalar(
        select(Usuario).where(Usuario.correo == formulario.username.strip().lower())
    )
    hash_guardado = usuario.password_hash if usuario else hash_ficticio()
    contrasena_correcta = verificar_password(formulario.password, hash_guardado)
    if usuario is None or not usuario.activo or not contrasena_correcta:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenSalida(access_token=crear_token(usuario), usuario=usuario)


@router.get("/perfil", response_model=UsuarioSalida)
def perfil(usuario: Usuario = Depends(get_usuario_actual)):
    """EP-03: datos del usuario autenticado."""
    return usuario
