import cv2
from camera_worker import CameraWorker

def callback_vacio(val):
    pass

def main():
    print("=======================================================")
    print(" INICIANDO PRUEBA Y DIAGNOSTICO DE CAPACIDADES DE CAMARA")
    print("=======================================================")

    try:
        worker = CameraWorker(camera_index=0)
    except Exception as e:
        print(f"[ERROR CRÍTICO] No se pudo iniciar el worker: {e}")
        return

    # Ejecutar la prueba de capacidades antes de abrir la interfaz
    print("\n[DIAGNOSTICO] Analizando soporte de hardware para la cámara...")
    capacidades = worker.detectar_capacidades()
    
    print("\n--- RESULTADO DE CAPACIDADES DE LA CÁMARA ---")
    for param, soportado in capacidades.items():
        estado = "SI SOPORTA" if soportado else "NO SOPORTA (Bloqueado por hardware/driver)"
        print(f" -> {param}: {estado}")
    print("---------------------------------------------\n")

    window_name = "Diagnostico de Camara y Sliders"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    for nombre_prop in worker.props.keys():
        val_inicial = worker.obtener_valor_propiedad_driver(nombre_prop)
        cv2.createTrackbar(nombre_prop, window_name, val_inicial, 255, callback_vacio)

    print("[INFO] Ventana abierta. Mueve los sliders para verificar si responden.")
    print("[INFO] Presiona la tecla 'q' para finalizar.\n")

    try:
        while True:
            worker.sincronizar_sliders(window_name)

            exito, frame = worker.obtener_frame_procesado(
                titulo="DIAGNOSTICO DE CAMARA - SLIDERS",
                subtitulo="Revisa la consola para ver qué parámetros acepta tu cámara"
            )

            if not exito or frame is None:
                print("[WARN] No se pudo obtener el fotograma.")
                break

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q')):
                print("[INFO] Finalizando la prueba...")
                break

    finally:
        print("[INFO] Liberando recursos...")
        worker.liberar_recursos()
        cv2.destroyAllWindows()
        print("[INFO] Prueba finalizada.")

if __name__ == "__main__":
    main()