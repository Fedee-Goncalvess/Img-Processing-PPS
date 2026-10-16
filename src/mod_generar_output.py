import glob
import os
import re
import threading

import cv2
import numpy as np

import config
from utils.ui_utils import HUDOverlay
from vision import get_vision


def extraer_orden_numerico(nombre_archivo):
    """Extrae los números del nombre para un ordenamiento secuencial correcto (img_2 < img_10)."""
    numeros = re.findall(r'\d+', nombre_archivo)
    return [int(n) for n in numeros] if numeros else [0]


class GeneradorOutputApp:
    def __init__(self, pics_folder=None, output_folder=None):
        self.vision = get_vision()
        self.pics_folder = pics_folder or config.PICS_FOLDER
        self.output_folder = output_folder or config.OUTPUT_FOLDER
        os.makedirs(self.output_folder, exist_ok=True)

    def cargar_imagenes_ordenadas(self, numero_corona=1):
        """Busca, filtra por corona y ordena secuencialmente las capturas."""
        if not os.path.exists(self.pics_folder):
            print(f"[ERROR] La carpeta de origen '{self.pics_folder}' no existe.")
            return [], []

        patron = os.path.join(self.pics_folder, f"corona_{numero_corona}_img_*.jpg")
        archivos = glob.glob(patron)
        archivos.sort(key=lambda p: extraer_orden_numerico(os.path.basename(p)))

        imagenes, rutas = [], []
        for ruta in archivos:
            img = self.vision.leer_imagen(ruta)
            if img is not None:
                imagenes.append(img)
                rutas.append(ruta)
        return imagenes, rutas

    def ejecutar_stitching_scan(self, numero_corona=1):
        """Stitching SCANS de una corona. Devuelve la ruta del resultado o None."""
        lineas = []

        def log(txt=""):
            print(txt)
            lineas.append(txt)

        log("\n=======================================================")
        log(f" MÓDULO GENERAR OUTPUT: STITCHING SCAN (Corona #{numero_corona})")
        log("=======================================================\n")

        imagenes, rutas = self.cargar_imagenes_ordenadas(numero_corona=numero_corona)
        if len(imagenes) < 2:
            log(f"[ERROR] Se necesitan al menos 2 imágenes para el stitching. "
                f"Se encontraron {len(imagenes)} para la corona {numero_corona}.")
            return None

        log(f"[STITCHING] Procesando {len(imagenes)} imágenes ordenadas (backend: {self.vision.nombre})...")
        res = self.vision.unir_imagenes(imagenes)

        if not res.ok:
            log("\n[ERROR STITCHING] Falló la composición global.")
            log(f"Motivo principal: {res.mensaje}")
            log("Ninguna imagen pudo ser unida con la configuración actual.\n")
            self._guardar_reporte(numero_corona, lineas)
            return None

        usadas = [rutas[i] for i in res.indices_usados]
        descartadas = [rutas[i] for i in range(len(rutas)) if i not in res.indices_usados]

        log("\n[REPORTE DE STITCHING]")
        log(f"✅ UTILIZADAS ({len(usadas)}/{len(rutas)}):")
        for r in usadas:
            log(f"  -> {os.path.basename(r)}")
        if descartadas:
            log(f"\n❌ DESCARTADAS ({len(descartadas)}/{len(rutas)}):")
            for r in descartadas:
                log(f"  -> {os.path.basename(r)}")
            log("  Motivo: Insuficiente solapamiento o falta de puntos clave (features) "
                "para enlazarse al panorama.")
        else:
            log("\n✅ Todas las imágenes fueron integradas exitosamente.")

        final = self.vision.recortar_bordes_negros(res.imagen)
        output_path = os.path.join(self.output_folder, f"composicion_corona_{numero_corona}.jpg")
        if not self.vision.guardar_imagen(output_path, final):
            log(f"[ERROR] No se pudo guardar {output_path}")
            self._guardar_reporte(numero_corona, lineas)
            return None

        log(f"\n[ÉXITO] Stitching guardado en: {output_path}\n")
        self._guardar_reporte(numero_corona, lineas)
        return output_path

    def _guardar_reporte(self, numero_corona, lineas):
        ruta = os.path.join(self.output_folder, f"reporte_corona_{numero_corona}.txt")
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(lineas))
        except OSError as e:
            print(f"[AVISO] No se pudo escribir el reporte: {e}")

    def generar_todo(self, total_coronas, callback=None):
        """Procesa las coronas 1..total_coronas. Devuelve {corona: ruta | None}."""
        resultados = {}
        for corona in range(1, total_coronas + 1):
            if callback:
                callback(corona, total_coronas)
            resultados[corona] = self.ejecutar_stitching_scan(numero_corona=corona)
        return resultados


# ======================================================================
# ETAPA COMPLETA CON INTERFAZ (invocada desde main.py)
# ======================================================================

def _canvas_visor(vision, ruta, mensaje_vacio):
    """Arma el lienzo del visor con la composición centrada (o un mensaje si no existe)."""
    ancho, alto = config.VISOR_MAX_ANCHO, config.VISOR_MAX_ALTO
    canvas = np.zeros((alto, ancho, 3), dtype=np.uint8)
    img = vision.leer_imagen(ruta) if ruta else None
    if img is None:
        cv2.putText(canvas, mensaje_vacio, (40, alto // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return canvas
    # Se deja margen para el HUD superior (90 px) e inferior (35 px)
    img = vision.redimensionar_para_ajustar(img, ancho, alto - 130)
    h, w = img.shape[:2]
    y = 90 + (alto - 125 - h) // 2
    x = (ancho - w) // 2
    canvas[y:y + h, x:x + w] = img
    return canvas


def _mostrar_resultados(window_name, resultados, vision):
    items = sorted(resultados.items())
    if not items:
        items = [(0, None)]

    for pos, (corona, ruta) in enumerate(items):
        canvas = _canvas_visor(vision, ruta, f"No se pudo generar la composicion de la corona {corona}.")
        ultimo = pos == len(items) - 1
        HUDOverlay.dibujar_encabezado(
            frame=canvas,
            titulo=f"RESULTADO: CORONA #{corona}" if corona else "RESULTADO",
            subtitulo=os.path.basename(ruta) if ruta else "Sin composición (ver reporte en output/)",
        )
        HUDOverlay.dibujar_barra_inferior(
            frame=canvas,
            texto_estado="[Cualquier tecla] " + ("Finalizar" if ultimo else "Siguiente corona") + " | [Q] Salir",
            porcentaje_progreso=(pos + 1) / len(items),
        )
        cv2.imshow(window_name, canvas)

        while True:
            key = cv2.waitKey(30) & 0xFF
            if key in (ord('q'), ord('Q')):
                return
            if key != 255:
                break


def ejecutar_generacion_output(window_name, total_coronas, tamano=(640, 480),
                               pics_folder=None, output_folder=None):
    """Corre el stitching en un hilo (la UI sigue respondiendo) y luego muestra los resultados."""
    app = GeneradorOutputApp(pics_folder=pics_folder, output_folder=output_folder)
    estado = {"hecho": False, "resultados": {}, "actual": 0, "error": None}

    def cb(corona, total):
        estado["actual"] = corona

    def worker():
        try:
            estado["resultados"] = app.generar_todo(total_coronas, callback=cb)
        except Exception as e:  # no dejar el hilo muerto en silencio
            estado["error"] = str(e)
            print(f"[ERROR] Falló la generación de output: {e}")
        finally:
            estado["hecho"] = True

    hilo = threading.Thread(target=worker, daemon=True)
    hilo.start()

    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    ancho, alto = tamano
    tick = 0
    while not estado["hecho"]:
        frame = np.zeros((alto, ancho, 3), dtype=np.uint8)
        HUDOverlay.dibujar_encabezado(
            frame=frame,
            titulo="ETAPA: GENERANDO OUTPUT Y REPORTES",
            subtitulo=f"Stitching corona {max(1, estado['actual'])}/{total_coronas}..." + "." * (tick // 5 % 4),
        )
        HUDOverlay.dibujar_barra_inferior(frame=frame, texto_estado="Estado: procesando imágenes acumuladas...")
        HUDOverlay.dibujar_barra_indeterminada(frame, tick)
        cv2.imshow(window_name, frame)
        cv2.waitKey(30)
        tick += 1
    hilo.join()

    _mostrar_resultados(window_name, estado["resultados"], app.vision)
    return estado["resultados"]


def exportar_reporte_ensayo(pics_folder=None, output_folder=None, total_coronas=1):
    """Punto de entrada sin UI (útil para scripts/tests)."""
    app = GeneradorOutputApp(pics_folder=pics_folder, output_folder=output_folder)
    return app.generar_todo(total_coronas)


if __name__ == "__main__":
    exportar_reporte_ensayo(total_coronas=1)