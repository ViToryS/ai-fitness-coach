
from __future__ import annotations

import argparse
import csv
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np


# Позволяет запускать скрипт непосредственно из папки experiments.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.pose_estimator import PoseEstimator
from src.exercises.squat.squat_phase_analyzer import SquatPhaseDetector


def calculate_knee_angle(landmarks):
    """Вычисляет средний угол левого и правого колена."""

    if landmarks is None:
        return None, None, None

    points = np.asarray(landmarks)

    if points.ndim != 2 or points.shape[0] < 29 or points.shape[1] < 4:
        return None, None, None

    angles = []
    visibilities = []

    for hip, knee, ankle in ((23, 25, 27), (24, 26, 28)):
        joints = points[[hip, knee, ankle]]

        visibility = float(np.min(joints[:, 3]))
        visibilities.append(visibility)

        if visibility < 0.5:
            continue

        a, b, c = joints[0, :2], joints[1, :2], joints[2, :2]

        ba = a - b
        bc = c - b

        denominator = np.linalg.norm(ba) * np.linalg.norm(bc)
        if denominator < 1e-6:
            continue

        cosine = np.dot(ba, bc) / denominator
        cosine = np.clip(cosine, -1.0, 1.0)

        angle = float(np.degrees(np.arccos(cosine)))
        angles.append(angle)

    if not angles:
        return None, None, None

    left_visibility = visibilities[0] if len(visibilities) > 0 else None
    right_visibility = visibilities[1] if len(visibilities) > 1 else None

    return (
        float(np.mean(angles)),
        left_visibility,
        right_visibility,
    )


def get_phase_name(phase):
    if phase is None:
        return "Поза не обнаружена"

    return getattr(phase, "name", str(phase))


def main():
    parser = argparse.ArgumentParser(
        description="Сбор диагностических данных для определения фаз приседания."
    )

    parser.add_argument("video", help="Путь к тестовому видео")
    parser.add_argument(
        "--viewpoint",
        default="unknown",
        choices=["front", "side", "diagonal", "unknown"],
        help="Ракурс видео",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Папка для результатов. По умолчанию experiments/results",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Не сохранять видео с диагностической информацией",
    )

    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"Видео не найдено: {video_path}")

    output_dir = Path(args.output) if args.output else (
        PROJECT_ROOT / "experiments" / "results"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    video_name = video_path.stem
    csv_path = output_dir / f"{video_name}_diagnostics.csv"
    output_video_path = output_dir / f"{video_name}_diagnostics.mp4"

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Не удалось открыть видео: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    pose_estimator = PoseEstimator()
    phase_detector = SquatPhaseDetector()

    # Используем внутреннее окно сглаживания детектора,
    # чтобы записывать именно тот угол, на котором основано решение о фазе.
    core_detector = phase_detector.detector
    angle_history = getattr(core_detector, "_angles", deque(maxlen=5))

    previous_angle = None
    previous_time = None

    writer = None
    if not args.no_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            str(output_video_path),
            fourcc,
            fps,
            (width, height),
        )

        if not writer.isOpened():
            cap.release()
            pose_estimator.close()
            raise RuntimeError("Не удалось создать выходное видео.")

    columns = [
        "frame",
        "time_sec",
        "viewpoint",
        "pose_detected",
        "left_visibility",
        "right_visibility",
        "raw_knee_angle",
        "smoothed_knee_angle",
        "angle_change",
        "angular_velocity_deg_sec",
        "phase",
    ]

    frame_index = 0
    valid_frames = 0
    phase_changes = []

    print(f"Видео: {video_path}")
    print(f"FPS: {fps:.2f}")
    print(f"Размер: {width}x{height}")
    print(f"Кадров в видео: {total_frames}")
    print("Начинаю анализ...")

    try:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=columns)
            csv_writer.writeheader()

            while True:
                success, frame = cap.read()
                if not success:
                    break

                timestamp = frame_index / fps

                landmarks = pose_estimator.process_frame(frame)

                raw_angle, left_visibility, right_visibility = (
                    calculate_knee_angle(landmarks)
                )

                phase = phase_detector.update(landmarks)
                phase_name = get_phase_name(phase)

                # Берём сглаженный угол из самого детектора.
                if raw_angle is not None and len(angle_history) > 0:
                    smoothed_angle = float(np.median(angle_history))
                    valid_frames += 1
                else:
                    smoothed_angle = None

                angle_change = None
                angular_velocity = None

                if smoothed_angle is not None:
                    if previous_angle is not None and previous_time is not None:
                        dt = timestamp - previous_time

                        if dt > 0:
                            angle_change = smoothed_angle - previous_angle
                            angular_velocity = angle_change / dt

                    previous_angle = smoothed_angle
                    previous_time = timestamp
                else:
                    previous_angle = None
                    previous_time = None

                csv_writer.writerow({
                    "frame": frame_index,
                    "time_sec": round(timestamp, 4),
                    "viewpoint": args.viewpoint,
                    "pose_detected": landmarks is not None,
                    "left_visibility": (
                        round(left_visibility, 4)
                        if left_visibility is not None else ""
                    ),
                    "right_visibility": (
                        round(right_visibility, 4)
                        if right_visibility is not None else ""
                    ),
                    "raw_knee_angle": (
                        round(raw_angle, 3) if raw_angle is not None else ""
                    ),
                    "smoothed_knee_angle": (
                        round(smoothed_angle, 3)
                        if smoothed_angle is not None else ""
                    ),
                    "angle_change": (
                        round(angle_change, 3)
                        if angle_change is not None else ""
                    ),
                    "angular_velocity_deg_sec": (
                        round(angular_velocity, 3)
                        if angular_velocity is not None else ""
                    ),
                    "phase": phase_name,
                })

                if phase_changes and phase_changes[-1]["phase"] != phase_name:
                    phase_changes.append({
                        "frame": frame_index,
                        "time": round(timestamp, 3),
                        "phase": phase_name,
                        "angle": smoothed_angle,
                        "velocity": angular_velocity,
                    })
                elif not phase_changes:
                    phase_changes.append({
                        "frame": frame_index,
                        "time": round(timestamp, 3),
                        "phase": phase_name,
                        "angle": smoothed_angle,
                        "velocity": angular_velocity,
                    })

                if writer is not None:
                    display = frame.copy()

                    angle_text = (
                        f"Angle: {smoothed_angle:.1f}"
                        if smoothed_angle is not None
                        else "Angle: N/A"
                    )
                    velocity_text = (
                        f"Velocity: {angular_velocity:.1f} deg/s"
                        if angular_velocity is not None
                        else "Velocity: N/A"
                    )

                    cv2.putText(
                        display,
                        f"Phase: {phase_name}",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        display,
                        angle_text,
                        (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 0),
                        2,
                    )
                    cv2.putText(
                        display,
                        velocity_text,
                        (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 0),
                        2,
                    )
                    cv2.putText(
                        display,
                        f"Frame: {frame_index}",
                        (20, 140),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                    )

                    writer.write(display)

                frame_index += 1

                if frame_index % 100 == 0:
                    print(f"Обработано кадров: {frame_index}/{total_frames}")

    finally:
        cap.release()
        if writer is not None:
            writer.release()
        pose_estimator.close()

    print("\nАнализ завершён.")
    print(f"Всего обработано кадров: {frame_index}")
    print(f"Кадров с обнаруженной позой: {valid_frames}")
    print(f"CSV: {csv_path}")

    if writer is not None:
        print(f"Видео: {output_video_path}")

    print("\nПереходы между фазами:")
    for item in phase_changes:
        print(
            f"Кадр {item['frame']:5d} | "
            f"{item['time']:7.3f} сек | "
            f"{item['phase']} | "
            f"угол: {item['angle']} | "
            f"скорость: {item['velocity']}"
        )


if __name__ == "__main__":
    main()
