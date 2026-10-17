# Alto nivel

import cv2
import numpy as np
from camera_driver import CameraDriver

class HUDOvertlay:
    """Dibuja encabezados, barras de estado y métricas unificadas sobre el frame."""
    
    @staticmethod
    def dibujar_encabezado(frame, titulo, subtitulo="", modo=""):
         h, w = frame.shape[:2]
         overlay = frame.copy()
         cv2.rectangle(overlay, (0, 0), (w, 90), (15, 15, 15), -1)
         cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

         cv2.putText(frame, titulo, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
         if subtitulo:
             cv2.putText(frame, subtitulo, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
         if modo:
             cv2.putText(frame, f"Modo: [{modo}]", (w - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    @staticmethod
    def dibujar_barra_inferior(frame, texto_estado, porcentaje_progreso=None):
         h, w = frame.shape[:2]
         cv2.rectangle(frame, (0, h - 35), (w, h), (30, 30, 30), -1)
         cv2.putText(frame, texto_estado, (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

         if porcentaje_progreso is not None:
             pct = max(0.0, min(1.0, porcentaje_progreso))
             cv2.rectangle(frame, (0, h - 5), (int(w * pct), h), (0, 255, 0), -1)

    @staticmethod
    def dibujar_barra_indeterminada(frame, tick):
         """Barra de progreso animada para tareas de duración desconocida."""
         h, w = frame.shape[:2]
         ancho_seg = max(1, w // 5)
         x = (tick * 12) % (w + ancho_seg) - ancho_seg
         cv2.rectangle(frame, (max(0, x), h - 5), (min(w, x + ancho_seg), h), (0, 255, 0), -1)

class VisionUtils:
    def __init__(self):
        self.motor = "OPENCV"

    @staticmethod
    def _a_gris(img):
        if img.ndim == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img     

    def calcular_brillo_medio(self,img) -> float:
        return float(np.mean(self._a_gris(img)))


    def calcular_nitidez_laplaciano(self, img) -> float:    
        return float(cv2.Laplacian(self._a_gris(img), cv2.CV_64F).var())


class CameraWorker:
    def __init__(self, camera_index=0):
        self.driver = CameraDriver(camera_index)
        self.driver.conectar()
        self.modo_actual = "EN VIVO"
        self.vision = VisionUtils()
        self.hud = HUDOvertlay()

    def obtener_frame_procesado(self, titulo= "SISTEMA DE VISIÓN", subtitulo= "Monitoreo activo"):
        ret, frame = self.driver.leer_frame_raw()
        if not ret or frame is None:
            return False, None

        brillo = self.vision.calcular_brillo_medio(frame)
        nitidez = self.vision.calcular_nitidez_laplaciano(frame)

        sub_completo = f"{subtitulo} | Brillo: {brillo:.1f} | Nitidez: {nitidez:.1f}"

        self.hud.dibujar_encabezado(
            frame=frame,
            titulo=titulo,
            subtitulo=sub_completo,
            modo=self.modo_actual
        )

        return True, frame

    def ajustar_configuracion_manual(self, exposicion=None, enfoque= None):
        if exposicion is not None:
            self.driver.set_propiedad(cv2.CAP_PROP_EXPOSURE, exposicion)
        if enfoque is not None:
                    self.driver.set_propiedad(cv2.CAP_PROP_FOCUS, enfoque)   

    def liberar_recursos(self):
        self.driver.desconectar()