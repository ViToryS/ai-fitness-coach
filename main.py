import os
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "1"
os.environ["OPENCV_VIDEOIO_PRIORITY_DSHOW"] = "1"

import sys
import cv2

cv2.setLogLevel(0) 

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())