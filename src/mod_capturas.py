import os
import time

import cv2

import config
from utils.ui_utils import HUDOverlay
from utils.camera_utils import resolver_camara, descartar_frames
from drivers.driver_cnc import cnc
from vision import get_vision


def calc_cant_pics():
    """Cantidad de imágenes a tomar durante la trayectoria."""
    return config.CANT_FOTOS


class CapturasApp:
    def __init__(self, cap, numero_corona=1, output_folder=None, window_name=None):
        self.numero_corona = numero_corona
        self.output_folder = output_folder or config.PICS_FOLDER
        self.owns_window = window_name is None
        self.window_name = window_name or f"Sistema de Vision - Capturas (Corona #{numero_corona})"
        self.vision = get_vision()

        os.makedirs(self.output_folder, exist_ok=True)
        self.cap, self.owns_cap = resolver_camara(cap)

    def ejecutar_secuencia_capturas(self):
        cant_fotos = calc_cant_pics()
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)

        print("\n=======================================================")
        print(f" MÓDULO CAPTURAS: INICIANDO BARRIDO (Corona #{self.numero_corona})")
        print("=======================================================\n")

        descartar_frames(self.cap, config.CAPTURAS_FRAMES_DESCARTE)

        foto_actual = 0
        estado_proceso = "TOMAR_FOTO"  # TOMAR_FOTO -> MOVIENDO -> ASENTANDO -> TOMAR_FOTO ... -> FINALIZADO
        estado_texto = "Preparando captura..."
        t_listo = 0.0
        resultado = "AVANZAR"

        while True:
            # Siempre leer la cámara: mantiene el video fluido y el buffer vacío
            ret, frame = self.cap.read()
            if not ret:
                print("[CAPTURAS] No se pudo leer de la cámara.")
                resultado = "SALIR"
                break

            if estado_proceso == "TOMAR_FOTO":
                foto_actual += 1
                filename = f"corona_{self.numero_corona}_img_{foto_actual}.jpg"
                filepath = os.path.join(self.output_folder, filename)

                # Se guarda ANTES de dibujar el HUD para no contaminar la imagen
                if not self.vision.guardar_imagen(filepath, frame):
                    print(f"[ERROR] No se pudo guardar {filepath}")
                    resultado = "SALIR"
                    break
                print(f"[CAPTURAS] Guardada: {filepath}")

                if foto_actual < cant_fotos:
                    cnc.iniciar_movimiento(direccion=1)
                    estado_proceso = "MOVIENDO"
                    estado_texto = "Moviendo riel... Esperando estado 'listo'"
                else:
                    estado_proceso = "FINALIZADO"
                    estado_texto = "¡Secuencia finalizada! Presiona 'N' para continuar."
                    print("\n[ÉXITO] Secuencia de capturas completada.")

            elif estado_proceso == "MOVIENDO":
                if cnc.obtener_estado() == "listo":
                    estado_proceso = "ASENTANDO"
                    t_listo = time.time()
                    estado_texto = "Estabilizando riel..."

            elif estado_proceso == "ASENTANDO":
                if time.time() - t_listo >= config.CNC_TIEMPO_ASENTAMIENTO:
                    estado_proceso = "TOMAR_FOTO"
                    estado_texto = "Tomando foto..."

            fotos_tomadas = min(foto_actual, cant_fotos)
            porcentaje = fotos_tomadas / cant_fotos if cant_fotos > 0 else 0.0

            HUDOverlay.dibujar_encabezado(
                frame=frame,
                titulo=f"ETAPA: ENSAYO - CAPTURAS (Corona #{self.numero_corona})",
                subtitulo=f"Captura: {fotos_tomadas} / {cant_fotos}",
            )
            HUDOverlay.dibujar_barra_inferior(
                frame=frame,
                texto_estado=f"Estado: {estado_texto} | [Q] Salir",
                porcentaje_progreso=porcentaje,
            )
            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q')):
                resultado = "SALIR"
                break
            elif key in (ord('n'), ord('N')) and estado_proceso == "FINALIZADO":
                break

        if self.owns_window:
            try:
                cv2.destroyWindow(self.window_name)
            except cv2.error:
                pass
        if self.owns_cap:
            self.cap.release()
        return resultado


def ejecutar_capturas(cap, numero_corona=1, output_folder=None, window_name=None):
    app = CapturasApp(cap=cap, numero_corona=numero_corona,
                      output_folder=output_folder, window_name=window_name)
    return app.ejecutar_secuencia_capturas()


if __name__ == "__main__":
    # Modo de prueba individual (crea y destruye su propia cámara)
    ejecutar_capturas(cap=0, numero_corona=1)