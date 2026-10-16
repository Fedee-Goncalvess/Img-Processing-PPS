"""Interfaz abstracta que todo backend de visión debe implementar (Adapter Pattern).

La lógica de negocio (módulos de etapa) solo habla con esta interfaz, de modo que
cambiar de librería de procesamiento de imágenes solo requiere un backend nuevo
y una línea en config.py.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class Marcador:
    """Marcador fiducial detectado (ej. ArUco)."""
    id: int
    esquinas: np.ndarray                 # (4, 2) en píxeles
    centro: Tuple[int, int] = (0, 0)


@dataclass
class ResultadoStitching:
    """Resultado normalizado del stitching, independiente de la librería."""
    ok: bool
    imagen: Optional[np.ndarray] = None
    indices_usados: List[int] = field(default_factory=list)
    mensaje: str = ""
    codigo: int = 0


class BaseVision(ABC):
    nombre = "base"

    # ---- Métricas fotométricas -------------------------------------------
    @abstractmethod
    def calcular_brillo_medio(self, img) -> float:
        """Brillo medio 0-255 (acepta imagen BGR o en gris)."""

    @abstractmethod
    def calcular_nitidez(self, img) -> float:
        """Métrica de enfoque (varianza del Laplaciano). Mayor = más nítida."""

    # ---- Entrada / salida de imágenes ------------------------------------
    @abstractmethod
    def leer_imagen(self, ruta: str):
        """Devuelve la imagen o None si no se pudo leer."""

    @abstractmethod
    def guardar_imagen(self, ruta: str, img) -> bool:
        """Guarda la imagen. Devuelve True si tuvo éxito."""

    @abstractmethod
    def redimensionar_para_ajustar(self, img, ancho_max: int, alto_max: int):
        """Reduce la imagen manteniendo proporción para que entre en el recuadro dado."""

    # ---- Procesamiento ----------------------------------------------------
    @abstractmethod
    def unir_imagenes(self, imagenes: list) -> ResultadoStitching:
        """Stitching de una secuencia ordenada de imágenes."""

    @abstractmethod
    def recortar_bordes_negros(self, img):
        """Elimina los bordes vacíos (negros) generados por el stitching."""

    @abstractmethod
    def detectar_marcadores(self, img) -> List[Marcador]:
        """Detecta marcadores fiduciales. Lista vacía si no hay o no está soportado."""