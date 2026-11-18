import time
import platform
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from src.core.pose_estimator import PoseEstimator
from src.core.skeleton_visualizer import draw_skeleton
import logging
log = logging.getLogger(__name__)

class CameraManager(QThread):
    frame_ready = Signal(np.ndarray)
    landmarks_ready = Signal(np.ndarray)
    error_occurred = Signal(str)

    def __init__(self, camera_index: int = 0, enable_pose: bool = True):
        super().__init__()
        self.camera_index = camera_index
        self.enable_pose = enable_pose
        self._is_running = False
        self.cap: Optional[cv2.VideoCapture] = None
        self.pose: Optional[PoseEstimator] = None

        self.frame_skip = 1
        self._frame_counter = 0

    def run(self):
        self._is_running = True

        if self.enable_pose:
            try:
                self.pose = PoseEstimator()
            except Exception as exc:
                self.error_occurred.emit(f"Ошибка инициализации позы: {exc}")
                self._is_running = False
                return

        backend = (
            cv2.CAP_DSHOW
            if platform.system() == "Windows"
            else cv2.CAP_ANY
        )
        self.cap = cv2.VideoCapture(self.camera_index, backend)

        if not self.cap.isOpened():
            self.error_occurred.emit(
                f"Не удалось открыть камеру {self.camera_index}."
            )
            self._cleanup()
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
            self._cleanup()
            return

        consecutive_errors = 0
        last_landmarks: Optional[np.ndarray] = None

        while self._is_running:
            try:
                ret, frame = self.cap.read()

                if not ret or frame is None:
                    consecutive_errors += 1
                    if consecutive_errors > 30:
                        self.error_occurred.emit(
                            "Камера перехвачена другим приложением! "
                            "Потерян видеопоток."
                        )
                        break
                    time.sleep(0.01)
                    continue

                if np.mean(frame) < 5.0:
                    consecutive_errors += 1
                    if consecutive_errors > 30:
                        self.error_occurred.emit(
                            "Камера перехвачена другим приложением! "
                            "Потерян видеопоток."
                        )
                        break
                    time.sleep(0.01)
                    continue

                consecutive_errors = 0

                self._frame_counter += 1
                should_process = (self._frame_counter % self.frame_skip) == 0

                if self.pose is not None and should_process:
                    try:
                        landmarks = self.pose.process_frame(frame)
                        if landmarks is not None:
                            last_landmarks = landmarks
                            frame = draw_skeleton(
                                frame,
                                landmarks,
                                visibility_threshold=self.pose.visibility_threshold,
                            )
                            self.landmarks_ready.emit(landmarks)
                    except Exception as exc:
                        print(f"[CameraManager] Ошибка pose: {exc}")

                elif self.pose is not None and last_landmarks is not None:
                    frame = draw_skeleton(
                        frame,
                        last_landmarks,
                        visibility_threshold=self.pose.visibility_threshold,
                    )

                self.frame_ready.emit(frame)
                time.sleep(0.01)

            except cv2.error as exc:
                self.error_occurred.emit(f"Критическая ошибка видеопотока: {exc}")
                break

        self._cleanup()

    def stop(self):
        self._is_running = False
        self.wait()

    def _cleanup(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            log.info("Ресурсы камеры %s освобождены.", self.camera_index)
        if self.pose is not None:
            self.pose.close()
            self.pose = None