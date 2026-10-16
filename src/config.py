"""Configuración global del sistema de visión y control de riel 2D."""
import os

# ---------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------
# Raíz del proyecto (carpeta que contiene a src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICS_FOLDER = os.path.join(BASE_DIR, "pics")        # capturas crudas
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")    # composiciones y reportes
LIMPIAR_PICS_AL_INICIAR = True                      # evita mezclar ensayos viejos con el actual

# ---------------------------------------------------------------
# VISIÓN (patrón Adapter)
# ---------------------------------------------------------------
# Backends disponibles: ver registro en vision/__init__.py
VISION_BACKEND = "opencv"

# ---------------------------------------------------------------
# CÁMARA
# ---------------------------------------------------------------
CAMERA_INDEX = 0
CAMERA_WIDTH = None          # None = resolución por defecto del dispositivo
CAMERA_HEIGHT = None
CAMERA_BUFFER_SIZE = 1       # buffer mínimo para evitar lag de frames

# ---------------------------------------------------------------
# INTERFAZ
# ---------------------------------------------------------------
VENTANA_PRINCIPAL = "Sistema de Vision - Control Principal"
VISOR_MAX_ANCHO = 1100       # tamaño máximo del visor de resultados
VISOR_MAX_ALTO = 620

# ---------------------------------------------------------------
# CNC / RIEL
# ---------------------------------------------------------------
CNC_SIMULADO = True
CNC_DURACION_SIMULADA = 3.0      # segundos que dura un movimiento simulado
CNC_TIEMPO_ASENTAMIENTO = 0.3    # espera tras "listo" para que se amortigüen vibraciones

# ---------------------------------------------------------------
# CAPTURAS
# ---------------------------------------------------------------
CANT_FOTOS = 5                   # fotos por corona
CAPTURAS_FRAMES_DESCARTE = 5     # frames descartados al iniciar (buffer viejo)

# ---------------------------------------------------------------
# POSICIONAMIENTO
# ---------------------------------------------------------------
ARUCO_DICCIONARIO = "DICT_4X4_50"
POS_TOLERANCIA_PX = 10           # error máximo (px) para considerar "alineado"

# ---------------------------------------------------------------
# STITCHING / RECORTE
# ---------------------------------------------------------------
STITCH_MODO = "SCANS"            # "SCANS" (riel rectilíneo) o "PANORAMA"
STITCH_CONFIDENCE_THRESH = 1.0   # bajar (ej. 0.3) si descarta imágenes con poco solape
CROP_UMBRAL_NEGRO = 5            # nivel de gris considerado "negro"
CROP_TOLERANCIA_NEGRO = 0.02     # fracción máxima de negro tolerada en cada borde