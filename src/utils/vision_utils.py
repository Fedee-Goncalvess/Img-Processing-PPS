"""Métricas de imagen compartidas. Delegan en el backend de visión activo."""
from vision import get_vision


def calcular_brillo_medio(img):
    """Brillo medio (0-255) de una imagen BGR o en gris."""
    return get_vision().calcular_brillo_medio(img)


def calcular_nitidez_laplaciano(img):
    """Nitidez como varianza del Laplaciano."""
    return get_vision().calcular_nitidez(img)