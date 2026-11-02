import sys
import cv2
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

from src.core.camera import CameraManager
from src.core.camera_utils import get_available_cameras
from src.infra.config_manager import save_camera_index, load_camera_index

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-Тренер")
        self.resize(800, 600)
        self.camera = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        controls_layout = QHBoxLayout()
        self.camera_combo = QComboBox()
        
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.populate_cameras)

        self.btn_start = QPushButton("Запустить")
        self.btn_stop = QPushButton("Остановить")
        self.btn_stop.setEnabled(False)

        self.populate_cameras()

        controls_layout.addWidget(QLabel("Камера:"))
        controls_layout.addWidget(self.camera_combo)
        controls_layout.addWidget(self.btn_refresh)
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        layout.addLayout(controls_layout)

        self.video_label = QLabel("Видео не запущено")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.video_label)

        self.btn_start.clicked.connect(self.start_camera)
        self.btn_stop.clicked.connect(self.stop_camera)

    def populate_cameras(self):
        self.btn_start.setEnabled(False)
        self.camera_combo.clear()
        
        cameras = get_available_cameras()
        
        if not cameras:
            self.camera_combo.addItem("Камеры не найдены", -1)
            return

        has_available = False
        for cam in cameras:
            idx = cam["index"]
            status = cam["status"]
            
            if status == "available":
                self.camera_combo.addItem(f"Камера {idx} (Доступна)", idx)
                has_available = True
            else:
                self.camera_combo.addItem(f"Камера {idx} (Занята другим ПО)", idx)
        
        if has_available:
            self.btn_start.setEnabled(True)
            saved_idx = load_camera_index()
            index = self.camera_combo.findData(saved_idx)
            if index >= 0:
                self.camera_combo.setCurrentIndex(index)
        else:
            self.btn_start.setEnabled(False)

    def start_camera(self):
        cam_idx = self.camera_combo.currentData()
        if cam_idx == -1: return

        current_text = self.camera_combo.currentText()
        if "Занята" in current_text:
            self.video_label.setText("ОШИБКА:\nВыбранная камера занята другим приложением.\nЗакройте его и нажмите 'Обновить'")
            return

        save_camera_index(cam_idx)

        self.camera = CameraManager(camera_index=cam_idx)
        self.camera.frame_ready.connect(self.update_frame)
        self.camera.error_occurred.connect(self.show_error)
        self.camera.start()

        self.btn_start.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.camera_combo.setEnabled(False)

    def stop_camera(self):
        if self.camera:
            self.camera.stop()
            self.camera = None
            self.video_label.clear()
            self.video_label.setText("Видео остановлено")
        
        self.btn_start.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.camera_combo.setEnabled(True)
        
        self.populate_cameras()

    def update_frame(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def show_error(self, message):
        self.video_label.setText(f"ОШИБКА:\n{message}")
        self.stop_camera()

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()