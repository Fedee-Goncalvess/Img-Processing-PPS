import cv2
import sys
BACKEND = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_V4L2

class CameraDriver:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

    def conectar(self):
        self.cap = cv2.VideoCapture(self.camera_index, BACKEND)
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"[ERROR DRIVER] No se pudo abrir la cámara con índice {self.camera_index}.")

        # Desactivar auto-enfoque y auto-exposición si el hardware lo permite para control manual
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) # 1 = Manual en V4L2
        
        return True    

    def leer_frame_raw(self):
        if self.cap and self.cap.isOpened():
            return self.cap.read()
        return False, None

    def set_propiedad(self, prop_id, valor):
        if self.cap and self.cap.isOpened():
            self.cap.set(prop_id, valor)

    def get_propiedad(self, prop_id):
        if self.cap and self.cap.isOpened():
            return self.cap.get(prop_id)
        return 0.0

    def desconectar(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()