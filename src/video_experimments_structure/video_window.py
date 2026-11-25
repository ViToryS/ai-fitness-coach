
import cv2
import numpy as np

from pathlib import Path
from src.exercises.base.analysis_event import (
    PhaseChanged,
    ViewpointChanged,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
)

from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

from src.ui.phase_panel import PhasePanel

from video_experimments_structure.video_manager import VideoManager

from src.exercises.registry import ExerciseRegistry
from src.exercises.squat.squat_exercise import SquatExercise


class VideoWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI-Тренер")
        self.resize(900, 650)

        self.video_path = None
        self.video = None
        self.is_paused = False
        self._stopping = False


        self.exercise_registry = ExerciseRegistry()
        self.exercise_registry.register(SquatExercise)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        controls_layout = QHBoxLayout()

        self.btn_select = QPushButton("Выбрать видео")
        self.btn_play = QPushButton("Воспроизвести")
        self.btn_pause = QPushButton("Пауза")
        self.btn_stop = QPushButton("Остановить")

        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

        controls_layout.addWidget(self.btn_select)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_stop)

        layout.addLayout(controls_layout)

        self.video_label = QLabel("Выберите видео для анализа")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setStyleSheet(
            "background-color: black; color: white;"
        )

        self.phase_panel = PhasePanel(
            exercises=[
                (exercise.id, exercise.name)
                for exercise in self.exercise_registry.list_exercises()
            ]
        )

        video_layout = QHBoxLayout()
        video_layout.addWidget(self.video_label, stretch=1)
        video_layout.addWidget(self.phase_panel)

        layout.addLayout(video_layout, stretch=1)

        self.btn_select.clicked.connect(self.select_video)
        self.btn_play.clicked.connect(self.play_video)
        self.btn_pause.clicked.connect(self.pause_video)
        self.btn_stop.clicked.connect(self.stop_video)

    def select_video(self):
        if self.video is not None and self.video.isRunning():
            self.stop_video()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите видео",
            "",
            "Видео (*.mp4 *.avi *.mov *.mkv *.wmv);;Все файлы (*)",
        )

        if not path:
            return

        self.video_path = path
        self.video_label.setText(f"Выбрано видео:\n{path}")

        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

    def play_video(self):
        if not self.video_path:
            return

        if self.video is not None and self.video.isRunning():
            self.video.resume()
            self.is_paused = False
            self.btn_pause.setText("Пауза")
            self.btn_pause.setEnabled(True)
            return

        exercise_id = self.phase_panel.selected_exercise_id

        if exercise_id is None:
            return

        exercise = self.exercise_registry.get(exercise_id)

        self.video = VideoManager(
            self.video_path,
            exercise
        )

        self.phase_panel.begin_video(
            Path(self.video_path).name
        )

        self.video.frame_ready.connect(self.update_frame)
        self.video.error_occurred.connect(self.show_error)
        self.video.finished.connect(self.on_video_finished)
        self.video.analysis_event.connect(
            self.handle_analysis_event
        )

        self.is_paused = False
        self._stopping = False

        self.video.start()
        self.phase_panel.set_exercise_selection_enabled(False)

        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

    def handle_analysis_event(self, event):
        if isinstance(event, PhaseChanged):
            self.phase_panel.set_phase(event.phase.name)

        elif isinstance(event, ViewpointChanged):
            self.phase_panel.add_viewpoint(
                event.viewpoint.value,
                event.count,
            )

    def pause_video(self):
        if self.video is None or not self.video.isRunning():
            return

        if self.is_paused:
            self.video.resume()
            self.btn_pause.setText("Пауза")
        else:
            self.video.pause()
            self.btn_pause.setText("Продолжить")

        self.is_paused = not self.is_paused

    def stop_video(self):
        self._stopping = True

        if self.video is not None and self.video.isRunning():
            self.video.stop()

        self.video = None
        self.is_paused = False

        self.video_label.clear()
        self.video_label.setText("Воспроизведение остановлено")

        self.btn_play.setEnabled(self.video_path is not None)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("Пауза")
        self.btn_stop.setEnabled(False)
        self.phase_panel.set_exercise_selection_enabled(True)
        self.phase_panel.reset()

    def update_frame(self, frame: np.ndarray):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        qt_image = QImage(
            rgb_image.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(qt_image)

        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def show_error(self, message: str):
        self.video_label.setText(f"ОШИБКА:\n{message}")

    def on_video_finished(self):
        self.btn_play.setEnabled(self.video_path is not None)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("Пауза")
        self.btn_stop.setEnabled(False)
        self.phase_panel.set_exercise_selection_enabled(True)
        self.is_paused = False

        if not self._stopping and self.video_label.pixmap() is not None:
            self.btn_play.setText("Повторить")

    def closeEvent(self, event):
        if self.video is not None and self.video.isRunning():
            self.video.stop()

        event.accept()
