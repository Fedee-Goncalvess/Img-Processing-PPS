"""Gestión centralizada de la cámara (instancia única de cv2.VideoCapture)."""
import cv2

import config


def abrir_camara(indice=None):
    """Abre la cámara (V4L2 si está disponible) y aplica la configuración global."""
    if indice is None:
        indice = config.CAMERA_INDEX

    cap = cv2.VideoCapture(indice, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(indice)
    if not cap.isOpened():
        raise RuntimeError(f"[ERROR CRÍTICO] No se pudo abrir la cámara con índice {indice}.")

    if config.CAMERA_WIDTH:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    if config.CAMERA_HEIGHT:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, config.CAMERA_BUFFER_SIZE)
    except Exception:
        pass
    return cap


def resolver_camara(cap):
    """Acepta un VideoCapture activo (no es dueño) o un índice (abre y es dueño).

    Devuelve (cap, owns_cap)."""
    if isinstance(cap, cv2.VideoCapture):
        return cap, False
    return abrir_camara(cap), True


def descartar_frames(cap, cantidad=3):
    """Lee y descarta frames para vaciar el buffer tras cambiar un parámetro."""
    for _ in range(max(0, cantidad)):
        cap.read()


def obtener_tamano(cap, defecto=(640, 480)):
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return (w, h) if w > 0 and h > 0 else defecto