from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_full/float16/latest/"
    "pose_landmarker_full.task"
)
MODEL_PATH = Path("models") / "pose_landmarker_full.task"

VISIBILITY_THRESHOLD = 0.6
SMOOTHING_ALPHA = 0.5


class PoseEstimator:

    def __init__(
        self,
        model_path: str | Path = MODEL_PATH,
        visibility_threshold: float = VISIBILITY_THRESHOLD,
        smoothing_alpha: float = SMOOTHING_ALPHA,
    ):
        self.visibility_threshold = visibility_threshold
        self.smoothing_alpha = smoothing_alpha
        self._prev_landmarks: Optional[np.ndarray] = None

        model_path = Path(model_path)
        self._ensure_model(model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: np.ndarray) -> Optional[np.ndarray]:

        h, w = frame_bgr.shape[:2]

        rgb = np.ascontiguousarray(frame_bgr[:, :, ::-1])
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb,
        )

        result = self._landmarker.detect(mp_image)

        if not result.pose_landmarks:
            self._prev_landmarks = None
            return None

        landmarks = result.pose_landmarks[0]

        raw = np.array(
            [
                [
                    lm.x,
                    lm.y,
                    lm.z,
                    getattr(lm, "visibility", getattr(lm, "presence", 0.0)),
                ]
                for lm in landmarks
            ],
            dtype=np.float32,
        )

        valid_mask = raw[:, 3] >= self.visibility_threshold

        if self._prev_landmarks is not None:
            raw[~valid_mask, :3] = self._prev_landmarks[~valid_mask, :3]

        if self._prev_landmarks is None:
            smoothed = raw.copy()
        else:
            smoothed = (
                self.smoothing_alpha * raw
                + (1.0 - self.smoothing_alpha) * self._prev_landmarks
            )

        smoothed[~valid_mask, :3] = raw[~valid_mask, :3]
        smoothed[:, 3] = raw[:, 3]

        self._prev_landmarks = smoothed
        return smoothed

    def get_landmarks(self) -> Optional[np.ndarray]:
        return self._prev_landmarks

    def close(self):
        try:
            self._landmarker.close()
        except Exception:
            pass

    @staticmethod
    def _ensure_model(model_path: Path):
        MIN_SIZE = 5_000_000

        if model_path.exists() and model_path.stat().st_size >= MIN_SIZE:
            return

        model_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[PoseEstimator] Скачивание модели: {MODEL_URL}")
        urllib.request.urlretrieve(MODEL_URL, model_path)

        size = model_path.stat().st_size
        if size < MIN_SIZE:
            model_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Модель скачалась некорректно (размер {size} байт). "
                f"Проверьте интернет/прокси и повторите запуск."
            )
        print(f"[PoseEstimator] Модель сохранена: {model_path} ({size} байт)")