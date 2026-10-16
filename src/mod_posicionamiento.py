import cv2
import numpy as np

import config
from utils.ui_utils import HUDOverlay
from utils.camera_utils import resolver_camara
from drivers.driver_cnc import cnc
from vision import get_vision


class PosicionamientoApp:
    def __init__(self, cap, numero_corona=1, window_name=None):
        self.numero_corona = numero_corona
        self.owns_window = window_name is None
        self.window_name = window_name or f"Sistema de Vision - Posicionamiento (Corona #{numero_corona})"
        self.cap, self.owns_cap = resolver_camara(cap)
        self.vision = get_vision()

    def procesar_alineacion(self, frame):
        """Dibuja la retícula central y los marcadores detectados.

        Devuelve True si hay un marcador dentro de la tolerancia de alineación."""
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        cv2.line(frame, (cx - 40, cy), (cx + 40, cy), (0, 255, 255), 1)
        cv2.line(frame, (cx, cy - 40), (cx, cy + 40), (0, 255, 255), 1)
        cv2.circle(frame, (cx, cy), 15, (0, 255, 255), 1)

        alineado = False
        for m in self.vision.detectar_marcadores(frame):
            cv2.polylines(frame, [m.esquinas.astype(np.int32).reshape(-1, 1, 2)], True, (0, 255, 0), 2)
            mx, my = m.centro
            error_x, error_y = mx - cx, my - cy
            cv2.line(frame, (cx, cy), (mx, my), (0, 0, 255), 2)
            cv2.putText(frame, f"ID {m.id} | DX: {error_x}px | DY: {error_y}px",
                        (mx + 10, my - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            if abs(error_x) <= config.POS_TOLERANCIA_PX and abs(error_y) <= config.POS_TOLERANCIA_PX:
                alineado = True
        return alineado

    def run(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)

        print("\n=======================================================")
        print(f" MÓDULO POSICIONAMIENTO: ALINEACIÓN RIEL (Corona #{self.numero_corona})")
        print("=======================================================")
        print(" -> 'A' / 'D': Mover riel izquierda / derecha")
        print(" -> 'N': Confirmar alineación y pasar a Capturas | 'Q': Salir")
        print("=======================================================\n")

        resultado = "AVANZAR"

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[POSICIONAMIENTO] No se pudo leer de la cámara.")
                resultado = "SALIR"
                break

            alineado = self.procesar_alineacion(frame)

            HUDOverlay.dibujar_encabezado(
                frame=frame,
                titulo=f"ETAPA: POSICIONAMIENTO Y ALINEACIÓN (Corona #{self.numero_corona})",
                subtitulo="ALINEADO con el marcador." if alineado
                else "Alinee la cámara con la trayectoria o marcador ArUco.",
            )
            HUDOverlay.dibujar_barra_inferior(
                frame=frame,
                texto_estado=f"CNC: [{cnc.obtener_estado()}] | [A/D] Mover | [N] Confirmar | [Q] Salir",
            )

            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('n'), ord('N')):
                print("[POSICIONAMIENTO] Alineación confirmada. Avanzando a Capturas...")
                resultado = "AVANZAR"
                break
            elif key in (ord('q'), ord('Q')):
                print("[POSICIONAMIENTO] Operación cancelada.")
                resultado = "SALIR"
                break
            elif key in (ord('a'), ord('A')):
                cnc.iniciar_movimiento(direccion=-1)
            elif key in (ord('d'), ord('D')):
                cnc.iniciar_movimiento(direccion=1)

        if self.owns_window:
            try:
                cv2.destroyWindow(self.window_name)
            except cv2.error:
                pass
        if self.owns_cap:
            self.cap.release()
        return resultado


def ejecutar_posicionamiento(cap=0, numero_corona=1, window_name=None):
    app = PosicionamientoApp(cap=cap, numero_corona=numero_corona, window_name=window_name)
    return app.run()


if __name__ == "__main__":
    ejecutar_posicionamiento(cap=0, numero_corona=1)