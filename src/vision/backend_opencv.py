"""Implementación concreta del motor de visión usando OpenCV."""
import cv2
import numpy as np

import config
from vision.base_vision import BaseVision, Marcador, ResultadoStitching


class BackendOpenCV(BaseVision):
    nombre = "opencv"

    _ERRORES_STITCH = {
        1: "Se necesitan más imágenes o mayor solapamiento entre tomas.",
        2: "Falló la estimación de homografía (insuficientes puntos clave coincidentes).",
        3: "Falló el ajuste de parámetros de cámara.",
    }

    def __init__(self):
        self._aruco_inicializado = False
        self._aruco_ok = False
        self._detector = None
        self._legacy = None

    # ---------------------------------------------------------------
    # Utilidades internas
    # ---------------------------------------------------------------
    @staticmethod
    def _a_gris(img):
        if img.ndim == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    # ---------------------------------------------------------------
    # Métricas
    # ---------------------------------------------------------------
    def calcular_brillo_medio(self, img) -> float:
        return float(np.mean(self._a_gris(img)))

    def calcular_nitidez(self, img) -> float:
        return float(cv2.Laplacian(self._a_gris(img), cv2.CV_64F).var())

    # ---------------------------------------------------------------
    # E/S
    # ---------------------------------------------------------------
    def leer_imagen(self, ruta: str):
        return cv2.imread(ruta)

    def guardar_imagen(self, ruta: str, img) -> bool:
        return bool(cv2.imwrite(ruta, img))

    def redimensionar_para_ajustar(self, img, ancho_max: int, alto_max: int):
        h, w = img.shape[:2]
        escala = min(ancho_max / w, alto_max / h, 1.0)
        if escala >= 1.0:
            return img
        nuevo = (max(1, int(w * escala)), max(1, int(h * escala)))
        return cv2.resize(img, nuevo, interpolation=cv2.INTER_AREA)

    # ---------------------------------------------------------------
    # Stitching
    # ---------------------------------------------------------------
    def unir_imagenes(self, imagenes: list) -> ResultadoStitching:
        if len(imagenes) < 2:
            return ResultadoStitching(False, mensaje="Se necesitan al menos 2 imágenes.", codigo=1)

        modo = cv2.Stitcher_SCANS if str(config.STITCH_MODO).upper() == "SCANS" else cv2.Stitcher_PANORAMA
        if hasattr(cv2, "Stitcher_create"):
            stitcher = cv2.Stitcher_create(modo)
        else:
            stitcher = cv2.Stitcher.create(modo)

        try:
            stitcher.setPanoConfidenceThresh(float(config.STITCH_CONFIDENCE_THRESH))
        except Exception:
            pass

        status, pano = stitcher.stitch(imagenes)

        if status != cv2.Stitcher_OK:
            msg = self._ERRORES_STITCH.get(int(status), f"Error no identificado (código {status}).")
            return ResultadoStitching(False, mensaje=msg, codigo=int(status))

        # Índices de las imágenes realmente integradas (varía según versión de OpenCV)
        try:
            indices = np.asarray(stitcher.component()).flatten().astype(int).tolist()
        except Exception:
            indices = []
        indices = [i for i in indices if 0 <= i < len(imagenes)]
        if not indices:
            # Versión sin component(): se asume que todas participaron
            indices = list(range(len(imagenes)))

        return ResultadoStitching(True, pano, sorted(set(indices)), "OK", 0)

    def recortar_bordes_negros(self, img):
        """Recorta el rectángulo útil: primero el bounding box del contenido y luego
        va recortando el lado con más negro hasta que todos los bordes quedan limpios."""
        gray = self._a_gris(img)
        mask = gray > int(config.CROP_UMBRAL_NEGRO)
        if not mask.any():
            return img

        filas = mask.any(axis=1)
        cols = mask.any(axis=0)
        y0 = int(np.argmax(filas))
        y1 = len(filas) - int(np.argmax(filas[::-1]))
        x0 = int(np.argmax(cols))
        x1 = len(cols) - int(np.argmax(cols[::-1]))

        sub = mask[y0:y1, x0:x1]
        t, b, l, r = 0, sub.shape[0], 0, sub.shape[1]
        tol = float(config.CROP_TOLERANCIA_NEGRO)

        while b - t > 1 and r - l > 1:
            negro = {
                "t": 1.0 - sub[t, l:r].mean(),
                "b": 1.0 - sub[b - 1, l:r].mean(),
                "l": 1.0 - sub[t:b, l].mean(),
                "r": 1.0 - sub[t:b, r - 1].mean(),
            }
            lado = max(negro, key=negro.get)
            if negro[lado] <= tol:
                break
            if lado == "t":
                t += 1
            elif lado == "b":
                b -= 1
            elif lado == "l":
                l += 1
            else:
                r -= 1

        if b - t <= 1 or r - l <= 1:
            return img[y0:y1, x0:x1]
        return img[y0 + t:y0 + b, x0 + l:x0 + r]

    # ---------------------------------------------------------------
    # Marcadores ArUco
    # ---------------------------------------------------------------
    def _inicializar_aruco(self):
        if self._aruco_inicializado:
            return
        self._aruco_inicializado = True
        try:
            aruco = cv2.aruco
            dict_id = getattr(aruco, config.ARUCO_DICCIONARIO)
            if hasattr(aruco, "ArucoDetector"):
                diccionario = aruco.getPredefinedDictionary(dict_id)
                self._detector = aruco.ArucoDetector(diccionario, aruco.DetectorParameters())
            else:  # OpenCV < 4.7
                self._legacy = (aruco.Dictionary_get(dict_id), aruco.DetectorParameters_create())
            self._aruco_ok = True
        except Exception as e:
            print(f"[VISION] ArUco no disponible ({e}). Se requiere opencv-contrib-python en versiones antiguas.")
            self._aruco_ok = False

    def detectar_marcadores(self, img):
        self._inicializar_aruco()
        if not self._aruco_ok:
            return []

        gray = self._a_gris(img)
        if self._detector is not None:
            corners, ids, _ = self._detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self._legacy[0], parameters=self._legacy[1])

        marcadores = []
        if ids is not None:
            for c, i in zip(corners, ids.flatten()):
                pts = c.reshape(4, 2)
                centro = pts.mean(axis=0)
                marcadores.append(Marcador(int(i), pts, (int(centro[0]), int(centro[1]))))
        return marcadores