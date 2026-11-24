
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from src.core.pose_estimator import PoseEstimator, MODEL_PATH

VISIBILITY_THRESHOLD = 0.6
SAMPLE_EVERY = 5


def calculate_features(landmarks, width, height):
    """Вычисляет геометрические признаки положения корпуса."""

    indices = [11, 12, 23, 24]

    points = np.array(
        [
            [
                landmarks[i].x,
                landmarks[i].y,
                landmarks[i].z,
                getattr(landmarks[i], "visibility", 0.0),
            ]
            for i in indices
        ],
        dtype=np.float32,
    )

    visibility = points[:, 3]
    visibility_min = float(np.min(visibility))

    result = {
        "visibility_min": visibility_min,
        "shoulder_width": None,
        "hip_width": None,
        "torso_height": None,
        "shoulder_width_ratio": None,
        "hip_width_ratio": None,
        "shoulder_depth": None,
        "hip_depth": None,
        "shoulder_depth_ratio": None,
        "hip_depth_ratio": None,
    }

    if visibility_min < VISIBILITY_THRESHOLD:
        return result

    left_shoulder, right_shoulder, left_hip, right_hip = points

    shoulder_width = abs(
        left_shoulder[0] - right_shoulder[0]
    ) * width

    hip_width = abs(
        left_hip[0] - right_hip[0]
    ) * width

    shoulder_center_y = (
        left_shoulder[1] + right_shoulder[1]
    ) / 2

    hip_center_y = (
        left_hip[1] + right_hip[1]
    ) / 2

    torso_height = abs(
        shoulder_center_y - hip_center_y
    ) * height

    if torso_height < 1:
        return result

    shoulder_depth = abs(
        left_shoulder[2] - right_shoulder[2]
    ) * width

    hip_depth = abs(
        left_hip[2] - right_hip[2]
    ) * width

    result.update({
        "shoulder_width": shoulder_width,
        "hip_width": hip_width,
        "torso_height": torso_height,
        "shoulder_width_ratio": shoulder_width / torso_height,
        "hip_width_ratio": hip_width / torso_height,
        "shoulder_depth": shoulder_depth,
        "hip_depth": hip_depth,
        "shoulder_depth_ratio": shoulder_depth / torso_height,
        "hip_depth_ratio": hip_depth / torso_height,
    })

    return result


def main():
    """Обрабатывает видео и сохраняет измерения в CSV."""

    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--label", default="unknown")
    parser.add_argument("--sample-every", type=int, default=SAMPLE_EVERY)
    args = parser.parse_args()

    if not args.video.exists():
        raise FileNotFoundError(args.video)

    if args.sample_every < 1:
        raise ValueError("sample-every должен быть не меньше 1")

    PoseEstimator._ensure_model(MODEL_PATH)

    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )

    landmarker = vision.PoseLandmarker.create_from_options(options)
    cap = cv2.VideoCapture(str(args.video))

    if not cap.isOpened():
        landmarker.close()
        raise RuntimeError(f"Не удалось открыть видео: {args.video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        fps = 30.0

    output_path = args.video.with_name(
        f"{args.video.stem}_viewpoint.csv"
    )

    columns = [
        "label",
        "frame",
        "time_sec",
        "visibility_min",
        "shoulder_width",
        "hip_width",
        "torso_height",
        "shoulder_width_ratio",
        "hip_width_ratio",
        "shoulder_depth",
        "hip_depth",
        "shoulder_depth_ratio",
        "hip_depth_ratio",
    ]

    valid_rows = []

    try:
        with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            frame_index = 0

            while True:
                success, frame = cap.read()

                if not success:
                    break

                if frame_index % args.sample_every == 0:
                    height, width = frame.shape[:2]

                    rgb = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )

                    mp_image = mp.Image(
                        image_format=mp.ImageFormat.SRGB,
                        data=np.ascontiguousarray(rgb),
                    )

                    result = landmarker.detect(mp_image)

                    if result.pose_landmarks:
                        features = calculate_features(
                            result.pose_landmarks[0],
                            width,
                            height,
                        )

                        row = {
                            "label": args.label,
                            "frame": frame_index,
                            "time_sec": round(frame_index / fps, 3),
                            **features,
                        }

                        writer.writerow(row)

                        if features["shoulder_width_ratio"] is not None:
                            valid_rows.append(features)

                frame_index += 1

    finally:
        cap.release()
        landmarker.close()

    print(f"\nВидео: {args.video.name}")
    print(f"Ракурс: {args.label}")
    print(f"Обработано кадров: {frame_index}")
    print(f"Кадров с пригодными точками: {len(valid_rows)}")
    print(f"Результат: {output_path}")

    if not valid_rows:
        print("Нет кадров с достаточной видимостью суставов.")
        return

    print("\nМедианные значения:")

    for key in [
        "shoulder_width_ratio",
        "hip_width_ratio",
        "shoulder_depth_ratio",
        "hip_depth_ratio",
    ]:
        values = [row[key] for row in valid_rows]
        print(f"{key}: {np.median(values):.4f}")


if __name__ == "__main__":
    main()
