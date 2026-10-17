
import cv2
from camera_worker import CameraWorker

def main():
    print("=======================================================")
    print(" INICIANDO PRUEBA DE ARQUITECTURA DRIVER-WORKER")
    print("=======================================================")

    # 1. Instanciar el Worker de alto nivel
    try:
        worker = CameraWorker(camera_index=0)
    except Exception as e:
        print(f"[ERROR CRÍTICO] No se pudo iniciar el worker: {e}")
        return

    window_name = "Test Driver-Worker"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    print("\n[INFO] Transmitiendo video. Presiona la tecla 'q' en la ventana para salir.\n")

    try:
        while True:
            # 2. La "interfaz" solicita el frame procesado al Worker
            exito, frame = worker.obtener_frame_procesado(
                titulo="MODULO: CAMARA (DRIVER-WORKER TEST)",
                subtitulo="Validando integracion"
            )

            if not exito or frame is None:
                print("[WARN] No se pudo obtener el fotograma.")
                break

            # 3. Mostrar el frame (Simulando lo que haría la GUI con el widget de video)
            cv2.imshow(window_name, frame)

            # Salir con la tecla 'Q'
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q')):
                print("[INFO] Saliendo de la prueba por solicitud del usuario.")
                break

    finally:
        # 4. Liberar recursos limpiamente
        print("[INFO] Liberando recursos del sistema...")
        worker.liberar_recursos()
        cv2.destroyAllWindows()
        print("[INFO] Prueba finalizada exitosamente.")

if __name__ == "__main__":
    main()