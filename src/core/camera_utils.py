import platform
import cv2
import time
import numpy as np


def get_available_cameras(max_cameras=2):
    cameras = []
    consecutive_failures = 0
    backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

    for index in range(max_cameras):
        try:
            cap = cv2.VideoCapture(index, backend)
        except cv2.error:
            consecutive_failures += 1
            if consecutive_failures >= 2:
                break
            continue

        if not cap.isOpened():
            cap.release()
            consecutive_failures += 1
            if consecutive_failures >= 2:
                break
            continue

        consecutive_failures = 0
        is_working = False
        for _ in range(5):
            ret, frame = cap.read()
            if ret and frame is not None and np.mean(frame) > 5.0:
                is_working = True
                break
            time.sleep(0.1)

        cameras.append({
            "index": index,
            "status": "available" if is_working else "busy",
        })
        cap.release()

    return cameras