"""Factory de backends de visión.

Lee config.VISION_BACKEND e instancia (una sola vez) el motor correspondiente.
Para sumar otra librería: crear backend_xxx.py que herede de BaseVision y
registrarlo en _BACKENDS (o con registrar_backend()).
"""
import importlib

import config
from vision.base_vision import BaseVision, Marcador, ResultadoStitching

# nombre -> (módulo, clase). La importación es perezosa: solo se carga el backend activo.
_BACKENDS = {
    "opencv": ("vision.backend_opencv", "BackendOpenCV"),
}

_instancia = None


def registrar_backend(nombre, modulo, clase):
    _BACKENDS[str(nombre).lower()] = (modulo, clase)


def get_vision() -> BaseVision:
    """Devuelve el motor de visión activo (singleton)."""
    global _instancia
    if _instancia is None:
        nombre = str(config.VISION_BACKEND).lower()
        if nombre not in _BACKENDS:
            raise ValueError(
                f"Backend de visión '{nombre}' desconocido. Disponibles: {list(_BACKENDS)}"
            )
        modulo, clase = _BACKENDS[nombre]
        _instancia = getattr(importlib.import_module(modulo), clase)()
        print(f"[VISION] Backend activo: {_instancia.nombre}")
    return _instancia


__all__ = ["get_vision", "registrar_backend", "BaseVision", "Marcador", "ResultadoStitching"]