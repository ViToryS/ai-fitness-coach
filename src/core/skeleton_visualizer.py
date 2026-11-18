import cv2
import numpy as np

POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12),
    (11, 13), (13, 15),
    (15, 17), (15, 19), (15, 21),
    (17, 19),
    (12, 14), (14, 16),
    (16, 18), (16, 20), (16, 22),
    (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (24, 26),
    (25, 27), (26, 28),
    (27, 29), (28, 30),
    (29, 31), (30, 32),
    (27, 31), (28, 32),
]

COLOR_POINT = (0, 255, 0)
COLOR_LINE = (0, 255, 255)
COLOR_LOW_CONF = (0, 0, 255)


def draw_skeleton(
    frame_bgr: np.ndarray,
    landmarks: np.ndarray,
    visibility_threshold: float = 0.6,
    point_radius: int = 4,
    line_thickness: int = 2,
) -> np.ndarray:

    h, w = frame_bgr.shape[:2]

    pts = np.zeros((33, 2), dtype=np.int32)
    vis = landmarks[:, 3]

    for i in range(33):
        x = int(landmarks[i, 0] * w)
        y = int(landmarks[i, 1] * h)
        pts[i] = (x, y)

    for start, end in POSE_CONNECTIONS:
        if vis[start] >= visibility_threshold and vis[end] >= visibility_threshold:
            cv2.line(
                frame_bgr,
                tuple(pts[start]),
                tuple(pts[end]),
                COLOR_LINE,
                line_thickness,
                cv2.LINE_AA,
            )

    for i in range(33):
        color = COLOR_POINT if vis[i] >= visibility_threshold else COLOR_LOW_CONF
        cv2.circle(
            frame_bgr,
            tuple(pts[i]),
            point_radius,
            color,
            -1,
            cv2.LINE_AA,
        )

    return frame_bgr