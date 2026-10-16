import cv2


class HUDOverlay:
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