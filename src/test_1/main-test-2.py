import cv2
from camera_worker import CameraWorker

def callback_vacio(val):
    pass

def main(): 
    try:
        cam = CameraWorker()
    except Exception as e:
        print(f"[ERROR CRÍTICO] No se pudo iniciar el worker: {e}")
        return

    try:
        while True:
            exito, frame = cam.obtener_frame_raw()

            if not exito or frame is None:
                print(f"[ERROR CRÍTICO] No se pudo iniciar el worker: {e}")
                break

            cv2.imshow("camara",frame)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord('q'), ord('Q')):
                print("[INFO] Finalizando la prueba...")
                break
            
    finally:
        print("[INFO] Liberando recursos...")
        cam.liberar_recursos()
        cv2.destroyAllWindows()
        print("[INFO] Prueba finalizada.")

if __name__ == "__main__":
    main()