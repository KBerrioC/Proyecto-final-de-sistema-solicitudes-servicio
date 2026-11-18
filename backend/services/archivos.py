"""Validación y almacenamiento de adjuntos (RNF-05)."""
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from ..config import configuracion

MAX_ARCHIVOS = 5
EXTENSIONES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
FIRMAS = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}
TAMANO_BLOQUE = 1024 * 1024


@dataclass
class ArchivoValidado:
    nombre_original: str
    extension: str
    tipo_mime: str
    contenido: bytes


def _limpiar_nombre(nombre: str) -> str:
    """Se queda solo con el nombre del archivo, sin rutas ni caracteres de control."""
    nombre = nombre.replace("\\", "/").split("/")[-1]
    nombre = re.sub(r"[\x00-\x1f\x7f]", "", nombre).strip()
    return nombre[:255] or "archivo"


def validar_archivo(archivo: UploadFile) -> ArchivoValidado:
    """Comprueba extensión, firma del contenido y tamaño. No escribe nada en disco."""
    nombre = _limpiar_nombre(archivo.filename or "")
    extension = Path(nombre).suffix.lower()
    tipo_mime = EXTENSIONES.get(extension)
    if tipo_mime is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"El archivo «{nombre}» no es PDF, JPG ni PNG",
        )
    limite = configuracion.max_upload_mb * 1024 * 1024
    contenido = bytearray()
    while True:
        bloque = archivo.file.read(TAMANO_BLOQUE)
        if not bloque:
            break
        contenido.extend(bloque)
        if len(contenido) > limite:
            raise HTTPException(
                413,
                f"El archivo «{nombre}» supera el máximo de {configuracion.max_upload_mb} MB",
            )
    if not contenido:
        raise HTTPException(422, f"El archivo «{nombre}» está vacío")
    if not any(contenido.startswith(firma) for firma in FIRMAS[tipo_mime]):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"El contenido de «{nombre}» no corresponde a su extensión",
        )
    extension_normalizada = ".jpg" if extension == ".jpeg" else extension
    return ArchivoValidado(nombre, extension_normalizada, tipo_mime, bytes(contenido))


def guardar_archivo(archivo: ArchivoValidado) -> str:
    """Guarda el archivo con un nombre aleatorio y devuelve ese nombre."""
    carpeta = Path(configuracion.upload_dir)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre_almacenado = f"{uuid.uuid4().hex}{archivo.extension}"
    (carpeta / nombre_almacenado).write_bytes(archivo.contenido)
    return nombre_almacenado


def eliminar_archivos(nombres: list[str]) -> None:
    for nombre in nombres:
        (Path(configuracion.upload_dir) / nombre).unlink(missing_ok=True)
