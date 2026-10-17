import cv2

class CameraDriver:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

    def conectar(self):
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"[ERROR DRIVER] No se pudo abrir la cámara con índice {self.camera_index}.")
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