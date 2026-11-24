
import time
import threading
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from src.core.pose_estimator import PoseEstimator
from src.core.skeleton_visualizer import draw_skeleton
from src.core.phase_detector import SquatPhaseDetector

class PoseWorker(QThread):
    error_occurred = Signal(str)
    phase_ready = Signal(str)

    def __init__(self):
        super().__init__()

        self._condition = threading.Condition()
        self._latest_frame = None
        self._running = True

        self._latest_landmarks = None
        self._last_detection_time = 0.0

    def submit_frame(self, frame: np.ndarray):
        with self._condition:
            self._latest_frame = frame.copy()
            self._condition.notify()

    def get_latest_landmarks(self):
        with self._condition:
            if self._latest_landmarks is None:
                return None, 0.0

            return (
                self._latest_landmarks.copy(),
                self._last_detection_time
            )

    def stop(self):
        with self._condition:
            self._running = False
            self._latest_frame = None
            self._condition.notify_all()

        self.wait()

    def run(self):
        pose = None

        try:

            pose = PoseEstimator()
            phase_detector = SquatPhaseDetector()
            last_phase = None
            while True:
                with self._condition:
                    while self._running and self._latest_frame is None:
                        self._condition.wait()

                    if not self._running:
                        break

                    frame = self._latest_frame
                    self._latest_frame = None

                landmarks = pose.process_frame(frame)

                phase = phase_detector.update(landmarks)

                if phase != last_phase:

                    self.phase_ready.emit(phase)
                    last_phase = phase

                if landmarks is not None:
                    with self._condition:
                        self._latest_landmarks = landmarks.copy()
                        self._last_detection_time = time.monotonic()

        except Exception as exc:
            self.error_occurred.emit(str(exc))

        finally:
            if pose is not None:
                pose.close()


class VideoManager(QThread):
    frame_ready = Signal(np.ndarray)
    error_occurred = Signal(str)
    phase_ready = Signal(str)

    LANDMARK_TIMEOUT = 0.3

    def __init__(self, video_path: str | Path):
        super().__init__()

        self.video_path = Path(video_path)

        self.cap: Optional[cv2.VideoCapture] = None
        self.pose_worker: Optional[PoseWorker] = None

        self._running = False
        self._play_event = threading.Event()
        self._play_event.set()

    def run(self):
        self._running = True

        try:
            self.cap = cv2.VideoCapture(str(self.video_path))

            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Не удалось открыть видео: {self.video_path}"
                )

            fps = self.cap.get(cv2.CAP_PROP_FPS)

            if not np.isfinite(fps) or fps <= 0:
                fps = 30.0

            frame_delay = 1.0 / fps
            next_frame_time = time.monotonic()

            self.pose_worker = PoseWorker()
            self.pose_worker.phase_ready.connect(
                self.forward_phase
            )

            self.pose_worker.error_occurred.connect(
                self.error_occurred.emit
            )
            self.pose_worker.start()

            while self._running:

                if not self._play_event.is_set():
                    while (
                        self._running
                        and not self._play_event.wait(0.1)
                    ):
                        pass

                    next_frame_time = time.monotonic()

                if not self._running:
                    break

                ret, frame = self.cap.read()

                if not ret:
                    break

                self.pose_worker.submit_frame(frame)

                landmarks, detection_time = (
                    self.pose_worker.get_latest_landmarks()
                )

                if (
                    landmarks is not None
                    and time.monotonic() - detection_time
                    <= self.LANDMARK_TIMEOUT
                ):
                    frame = draw_skeleton(
                        frame,
                        landmarks,
                        visibility_threshold=self.pose_worker_visibility_threshold
                    )

                self.frame_ready.emit(frame)

                next_frame_time += frame_delay

                while self._running and self._play_event.is_set():
                    remaining = next_frame_time - time.monotonic()

                    if remaining <= 0:
                        break

                    time.sleep(min(remaining, 0.005))

        except Exception as exc:
            self.error_occurred.emit(str(exc))

        finally:
            self._cleanup()

    @property
    def pose_worker_visibility_threshold(self):
        return 0.6

    def pause(self):
        self._play_event.clear()

    def resume(self):
        self._play_event.set()

    def stop(self):
        self._running = False
        self._play_event.set()
        self.wait()

    def _cleanup(self):
        self._running = False

        if self.pose_worker is not None:
            self.pose_worker.stop()
            self.pose_worker = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def forward_phase(self, phase):
        self.phase_ready.emit(phase)