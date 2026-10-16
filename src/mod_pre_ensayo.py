import cv2

from utils.vision_utils import calcular_brillo_medio, calcular_nitidez_laplaciano
from utils.ui_utils import HUDOverlay
from utils.camera_utils import resolver_camara, descartar_frames


def callback_vacio(val):
    """Callback requerido por cv2.createTrackbar."""
    pass


class PreEnsayoCameraApp:
    def __init__(self, cap=0, numero_corona=1, window_name=None):
        self.numero_corona = numero_corona
        # Ventana principal compartida (si no se pasa, el módulo crea y destruye la suya)
        self.owns_window = window_name is None
        self.window_name = window_name or f"Sistema de Vision - Pre-Ensayo (Corona #{numero_corona})"
        # Los deslizadores viven en una ventana aparte para poder cerrarlos al salir de la etapa
        self.window_controles = "Controles de Camara"

        self.modo_actual = "MANUAL"
        self.status_msg = "Presiona '1': Auto | '2': Manual | 'N': Avanzar de Etapa."

        self.cap, self.owns_cap = resolver_camara(cap)

        # Desactivar automatismos de hardware para permitir control manual
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 1 = Manual en V4L2 / Linux

        self.props = {
            "Exposicion": cv2.CAP_PROP_EXPOSURE,
            "Enfoque": cv2.CAP_PROP_FOCUS,
            "Brillo": cv2.CAP_PROP_BRIGHTNESS,
            "Contraste": cv2.CAP_PROP_CONTRAST,
            "Ganancia": cv2.CAP_PROP_GAIN,
        }

        # Valor mostrado y último valor realmente enviado a la cámara (para no pisarla sin cambios)
        self.valores = {k: self._leer_clamp(p) for k, p in self.props.items()}
        self._aplicados = dict(self.valores)

    def _leer_clamp(self, prop_id):
        return max(0, min(int(self.cap.get(prop_id)), 255))

    def crear_trackbars_manuales(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        cv2.namedWindow(self.window_controles, cv2.WINDOW_NORMAL)
        for nombre in self.props:
            cv2.createTrackbar(nombre, self.window_controles, self.valores[nombre], 255, callback_vacio)
        try:
            cv2.resizeWindow(self.window_controles, 420, 220)
        except Exception:
            pass

    def _refrescar_frame(self, n=3):
        """Descarta frames viejos y devuelve uno fresco tras cambiar un parámetro."""
        descartar_frames(self.cap, n)
        ret, frame = self.cap.read()
        return frame if ret else None

    def ejecutar_auto_configuracion(self):
        """1: Auto-exposición por retroalimentación de brillo + barrido de enfoque."""
        self.status_msg = "Ejecutando algoritmo de auto-configuracion..."

        # 1. Auto-exposición
        target_brillo = 128.0
        exp_val = self.cap.get(cv2.CAP_PROP_EXPOSURE)

        for _ in range(12):
            frame = self._refrescar_frame(2)
            if frame is None:
                break
            diff = target_brillo - calcular_brillo_medio(frame)
            if abs(diff) < 8:
                break
            exp_val += (15.0 if diff > 0 else -15.0)
            self.cap.set(cv2.CAP_PROP_EXPOSURE, exp_val)

        # 2. Auto-enfoque por barrido de varianza Laplaciana
        mejor_focus, max_nitidez = 0, -1.0
        for f in range(0, 255, 15):
            self.cap.set(cv2.CAP_PROP_FOCUS, f)
            frame = self._refrescar_frame(3)
            if frame is None:
                continue
            nitidez = calcular_nitidez_laplaciano(frame)
            if nitidez > max_nitidez:
                max_nitidez, mejor_focus = nitidez, f
        self.cap.set(cv2.CAP_PROP_FOCUS, mejor_focus)

        # Sincronizar deslizadores con lo que quedó en la cámara
        for nombre, prop_id in self.props.items():
            val = self._leer_clamp(prop_id)
            self.valores[nombre] = val
            self._aplicados[nombre] = val
            try:
                cv2.setTrackbarPos(nombre, self.window_controles, val)
            except Exception:
                pass

        self.status_msg = f"Auto-configuracion completada (enfoque={mejor_focus}, nitidez={max_nitidez:.1f})."

    def actualizar_parametros_manuales(self):
        """2: aplica a la cámara solo los deslizadores que cambiaron."""
        for nombre, prop_id in self.props.items():
            try:
                pos = cv2.getTrackbarPos(nombre, self.window_controles)
            except Exception:
                continue
            if pos != -1 and pos != self._aplicados[nombre]:
                self.cap.set(prop_id, pos)
                self._aplicados[nombre] = pos
                self.valores[nombre] = pos

    def dibujar_interface_hud(self, frame, brillo_med, nitidez_val):
        HUDOverlay.dibujar_encabezado(
            frame=frame,
            titulo=f"ETAPA: PRE-ENSAYO (Corona #{self.numero_corona})",
            subtitulo=f"Brillo Medio: {brillo_med:.1f} / 255 | Nitidez: {nitidez_val:.1f}",
            modo=self.modo_actual,
        )
        texto_params = " | ".join([f"{k}: {v}" for k, v in self.valores.items()])
        cv2.putText(frame, f"Valores Hardware -> {texto_params}",
                    (15, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        HUDOverlay.dibujar_barra_inferior(
            frame=frame,
            texto_estado=f"[1] Auto | [2] Manual | [N] Siguiente Etapa | [Q] Salir | {self.status_msg}",
        )

    def run(self):
        self.crear_trackbars_manuales()

        print("\n=======================================================")
        print(f" MÓDULO PRE-ENSAYO: CONFIGURACIÓN CÁMARA (Corona #{self.numero_corona})")
        print("=======================================================")
        print(" -> '1': Ajuste Automático | '2': Modo Manual (sliders)")
        print(" -> 'N': Avanzar a Posicionamiento | 'Q': Salir")
        print("=======================================================\n")

        resultado = "AVANZAR"

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[PRE-ENSAYO] No se pudo leer de la cámara.")
                resultado = "SALIR"
                break

            brillo = calcular_brillo_medio(frame)
            nitidez = calcular_nitidez_laplaciano(frame)

            if self.modo_actual == "MANUAL":
                self.actualizar_parametros_manuales()

            self.dibujar_interface_hud(frame, brillo, nitidez)
            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('n'), ord('N')):
                print("[PRE-ENSAYO] Parámetros guardados. Avanzando a Posicionamiento...")
                resultado = "AVANZAR"
                break
            elif key in (ord('q'), ord('Q')):
                print("[PRE-ENSAYO] Operación cancelada por el usuario.")
                resultado = "SALIR"
                break
            elif key == ord('1'):
                self.modo_actual = "AUTOMATICO"
                # Mostrar el mensaje antes de bloquear con el algoritmo
                self.status_msg = "Ejecutando algoritmo de auto-configuracion..."
                self.dibujar_interface_hud(frame, brillo, nitidez)
                cv2.imshow(self.window_name, frame)
                cv2.waitKey(1)
                self.ejecutar_auto_configuracion()
            elif key == ord('2'):
                self.modo_actual = "MANUAL"
                self.status_msg = "Modo Manual activo. Usa los deslizadores."

        self._limpiar()
        return resultado

    def _limpiar(self):
        try:
            cv2.destroyWindow(self.window_controles)
        except cv2.error:
            pass
        if self.owns_window:
            try:
                cv2.destroyWindow(self.window_name)
            except cv2.error:
                pass
        if self.owns_cap:
            self.cap.release()


def ejecutar_pre_ensayo(cap=0, numero_corona=1, window_name=None):
    """Función invocada desde main.py para ejecutar esta etapa."""
    app = PreEnsayoCameraApp(cap=cap, numero_corona=numero_corona, window_name=window_name)
    return app.run()


if __name__ == "__main__":
    ejecutar_pre_ensayo(cap=0, numero_corona=1)