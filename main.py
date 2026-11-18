import os
import warnings

os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "1"
os.environ["OPENCV_VIDEOIO_PRIORITY_DSHOW"] = "1"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ABSL_MIN_LOG_LEVEL"] = "2"

warnings.filterwarnings(
    "ignore",
    message=".*SymbolDatabase\\.GetPrototype\\(\\).*",
)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="google\\.protobuf.*",
)

import sys
import cv2

try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
except Exception:
    pass

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())