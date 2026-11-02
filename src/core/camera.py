import cv2
import numpy as np
import time
from PySide6.QtCore import QThread, Signal
import platform

class CameraError(Exception):
    pass

class CameraManager(QThread):
    frame_ready = Signal(np.ndarray)
    error_occurred = Signal(str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._is_running = False
        self.cap = None

    def run(self):
        self._is_running = True
        
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(self.camera_index, backend)

        if not self.cap.isOpened():
            self.error_occurred.emit(f"Не удалось открыть камеру {self.camera_index}.")
            self._is_running = False
            return

        time.sleep(1.0)

        start_success = False
        for _ in range(10):
            ret, frame = self.cap.read()
            if ret and frame is not None and np.mean(frame) > 5.0:
                start_success = True
                break
            time.sleep(0.1)

        if not start_success:
            self.error_occurred.emit("Камера занята другим приложением.")
            self.release()
            self._is_running = False
            return

        self.frame_ready.emit(frame)

        consecutive_errors = 0
        while self._is_running:
            try:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    consecutive_errors += 1
                else:
                    if np.mean(frame) < 5.0:
                        consecutive_errors += 1
                    else:
                        consecutive_errors = 0
                        self.frame_ready.emit(frame)

                if consecutive_errors > 30:
                    self.error_occurred.emit("Камера перехвачена другим приложением! Потерян видеопоток.")
                    break
                
                time.sleep(0.01)
            except cv2.error:
                self.error_occurred.emit("Критическая ошибка видеопотока.")
                break

        self.release()

    def stop(self):
        self._is_running = False
        self.wait()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print(f"Ресурсы камеры {self.camera_index} освобождены.")