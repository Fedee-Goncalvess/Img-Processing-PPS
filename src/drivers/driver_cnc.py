"""Interfaz no bloqueante con el CNC del riel 2D (con modo simulado)."""
import time

import config


class ControladorCNC:
    def __init__(self, es_simulado=True, duracion_simulada=3.0):
        self.es_simulado = es_simulado
        self.duracion_simulada = duracion_simulada
        self.tiempo_inicio = 0.0
        self.en_movimiento = False
        self.posicion = 0           # pasos acumulados (simulado)
        self._direccion = 1

    def iniciar_movimiento(self, direccion=1):
        """Envía la orden de mover un paso (+1 derecha / -1 izquierda).

        Devuelve False si ya hay un movimiento en curso (se ignora la orden)."""
        if self.en_movimiento:
            print("[DRIVER CNC] Movimiento en curso, orden ignorada.")
            return False

        print(f"[DRIVER CNC] Orden de movimiento enviada al riel (dir={direccion:+d})...")
        self._direccion = direccion
        self.tiempo_inicio = time.time()
        self.en_movimiento = True
        if not self.es_simulado:
            self._enviar_orden_hardware(direccion)
        return True

    def obtener_estado(self):
        """'listo' si el riel está quieto, 'pendiente' si sigue moviéndose."""
        if not self.en_movimiento:
            return "listo"

        if self.es_simulado:
            terminado = (time.time() - self.tiempo_inicio) >= self.duracion_simulada
        else:
            terminado = self._consultar_hardware()

        if terminado:
            print("[DRIVER CNC] Movimiento completado.")
            self.en_movimiento = False
            self.posicion += self._direccion
            return "listo"
        return "pendiente"

    def detener(self):
        self.en_movimiento = False

    # --- Ganchos para el hardware real (serie / GRBL / etc.) ---
    def _enviar_orden_hardware(self, direccion):
        raise NotImplementedError("Implementar comunicación con el CNC real.")

    def _consultar_hardware(self):
        raise NotImplementedError("Implementar consulta de estado del CNC real.")


# Instancia global por defecto
cnc = ControladorCNC(es_simulado=config.CNC_SIMULADO,
                     duracion_simulada=config.CNC_DURACION_SIMULADA)