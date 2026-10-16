import glob
import os
import time
from enum import Enum, auto

import cv2

import config
import mod_pre_ensayo
import mod_posicionamiento
import mod_capturas
import mod_generar_output
from drivers.driver_cnc import cnc
from utils.camera_utils import abrir_camara, obtener_tamano
from utils.ui_utils import HUDOverlay
from vision import get_vision


# ==========================================
# DEFINICIÓN DE ESTADOS (MÁQUINA DE ESTADOS)
# ==========================================
class EstadoEnsayo(Enum):
    PRE_ENSAYO = auto()
    POSICIONAMIENTO = auto()
    CAPTURAS = auto()
    SELECCION_FIN = auto()
    SIGUIENTE_CORONA = auto()
    GENERANDO_OUTPUT = auto()
    FINALIZADO = auto()


class ControlSistemaVision:
    def __init__(self, camera_index=None):
        self.camera_index = config.CAMERA_INDEX if camera_index is None else camera_index
        self.estado_actual = EstadoEnsayo.PRE_ENSAYO
        self.numero_corona = 1
        self.running = True
        self.window_name = config.VENTANA_PRINCIPAL

        get_vision()  # valida el backend configurado al arrancar

        if config.LIMPIAR_PICS_AL_INICIAR:
            self._limpiar_pics()

        # --- APERTURA ÚNICA DE LA CÁMARA Y DE LA VENTANA ---
        print(f"[SISTEMA] Inicializando cámara index={self.camera_index}...")
        self.cap = abrir_camara(self.camera_index)
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)

    @staticmethod
    def _limpiar_pics():
        """Borra capturas de ensayos anteriores para no mezclarlas con el actual."""
        for ruta in glob.glob(os.path.join(config.PICS_FOLDER, "corona_*_img_*.jpg")):
            try:
                os.remove(ruta)
            except OSError:
                pass

    @staticmethod
    def _transicion(resultado, siguiente):
        """Cada módulo devuelve 'AVANZAR' o 'SALIR'."""
        return siguiente if resultado == "AVANZAR" else EstadoEnsayo.FINALIZADO

    # ------------------------------------------------------------------
    # ESTADOS
    # ------------------------------------------------------------------
    def ejecutar_estado_pre_ensayo(self):
        print(f"\n[ESTADO] === ETAPA: PRE-ENSAYO (Corona #{self.numero_corona}) ===")
        resultado = mod_pre_ensayo.ejecutar_pre_ensayo(
            self.cap, self.numero_corona, window_name=self.window_name)
        return self._transicion(resultado, EstadoEnsayo.POSICIONAMIENTO)

    def ejecutar_estado_posicionamiento(self):
        print(f"\n[ESTADO] === ETAPA: ENSAYO - POSICIONAMIENTO (Corona #{self.numero_corona}) ===")
        resultado = mod_posicionamiento.ejecutar_posicionamiento(
            self.cap, self.numero_corona, window_name=self.window_name)
        return self._transicion(resultado, EstadoEnsayo.CAPTURAS)

    def ejecutar_estado_capturas(self):
        print(f"\n[ESTADO] === ETAPA: ENSAYO - CAPTURAS (Corona #{self.numero_corona}) ===")
        resultado = mod_capturas.ejecutar_capturas(
            cap=self.cap, numero_corona=self.numero_corona, window_name=self.window_name)
        return self._transicion(resultado, EstadoEnsayo.SELECCION_FIN)

    def ejecutar_estado_seleccion_fin(self):
        print("\n[ESTADO] === ETAPA: SELECCIÓN DE FIN ===")
        return self._pantalla_espera_transicion(
            titulo="ETAPA: COMPLETADA",
            subtitulo="Corona finalizada. ¿Repetir con otra corona o terminar el ensayo?",
            teclas_permitidas={
                'r': (EstadoEnsayo.SIGUIENTE_CORONA, "Repetir (Siguiente Corona)"),
                't': (EstadoEnsayo.GENERANDO_OUTPUT, "Terminar Ensayo"),
            },
        )

    def ejecutar_estado_siguiente_corona(self):
        self.numero_corona += 1
        print(f"\n[TRANSICIÓN] Preparando Siguiente Corona -> Corona #{self.numero_corona}")
        time.sleep(0.5)
        return EstadoEnsayo.POSICIONAMIENTO

    def ejecutar_estado_generando_output(self):
        print("\n[ESTADO] === ETAPA: GENERANDO OUTPUT ===")
        mod_generar_output.ejecutar_generacion_output(
            window_name=self.window_name,
            total_coronas=self.numero_corona,
            tamano=obtener_tamano(self.cap),
        )
        print("\n[ÉXITO] Generación de output completada. Finalizando programa.")
        return EstadoEnsayo.FINALIZADO

    # ------------------------------------------------------------------
    # PANTALLA DE ESPERA COMÚN
    # ------------------------------------------------------------------
    def _pantalla_espera_transicion(self, titulo, subtitulo, teclas_permitidas):
        """teclas_permitidas: {'r': (EstadoDestino, 'Etiqueta')}"""
        opciones_str = " | ".join(f"[{k.upper()}] {etiqueta}" for k, (_, etiqueta) in teclas_permitidas.items())

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] No se pudo leer de la cámara.")
                return EstadoEnsayo.FINALIZADO

            HUDOverlay.dibujar_encabezado(frame=frame, titulo=titulo, subtitulo=subtitulo)
            HUDOverlay.dibujar_barra_inferior(
                frame=frame, texto_estado=f"{opciones_str} | [Q] Salir")
            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q')):
                self.running = False
                return EstadoEnsayo.FINALIZADO
            for char_tecla, (estado_destino, _) in teclas_permitidas.items():
                if key in (ord(char_tecla.lower()), ord(char_tecla.upper())):
                    return estado_destino

    # ------------------------------------------------------------------
    # BUCLE PRINCIPAL
    # ------------------------------------------------------------------
    def iniciar(self):
        print("\n=======================================================")
        print(" INICIANDO SISTEMA DE VISIÓN Y CONTROL DE RIEL 2D")
        print("=======================================================")

        despachador = {
            EstadoEnsayo.PRE_ENSAYO: self.ejecutar_estado_pre_ensayo,
            EstadoEnsayo.POSICIONAMIENTO: self.ejecutar_estado_posicionamiento,
            EstadoEnsayo.CAPTURAS: self.ejecutar_estado_capturas,
            EstadoEnsayo.SELECCION_FIN: self.ejecutar_estado_seleccion_fin,
            EstadoEnsayo.SIGUIENTE_CORONA: self.ejecutar_estado_siguiente_corona,
            EstadoEnsayo.GENERANDO_OUTPUT: self.ejecutar_estado_generando_output,
        }

        try:
            while self.running and self.estado_actual != EstadoEnsayo.FINALIZADO:
                self.estado_actual = despachador[self.estado_actual]()
        finally:
            print("[SISTEMA] Cerrando cámara y liberando recursos...")
            cnc.detener()
            if self.cap.isOpened():
                self.cap.release()
            cv2.destroyAllWindows()
            print("\nPrograma finalizado correctamente.")


if __name__ == "__main__":
    app = ControlSistemaVision()
    app.iniciar()