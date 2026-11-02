import cv2
import time
import numpy as np

def get_available_cameras(max_cameras=3):
    cameras = []
    
    for index in range(max_cameras):
        cap = cv2.VideoCapture(index)
        
        if cap.isOpened():
            is_working = False
            for _ in range(5):
                ret, frame = cap.read()
                if ret and frame is not None and np.mean(frame) > 5.0:
                    is_working = True
                    break
                time.sleep(0.1)
            
            if is_working:
                cameras.append({"index": index, "status": "available"})
            else:
                cameras.append({"index": index, "status": "busy"})
                
            cap.release()
            
    return cameras