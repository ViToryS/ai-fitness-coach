
import time

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
)
from PySide6.QtCore import Qt


class PhasePanel(QWidget):

    def __init__(self):
        super().__init__()

        self.current_phase = None
        self.phase_start_time = None

        self.setMinimumWidth(240)
        self.setMaximumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        title = QLabel("Текущая фаза")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold;"
        )

        self.phase_label = QLabel("Ожидание упражнения")
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setWordWrap(True)
        self.phase_label.setMinimumHeight(90)
        self.phase_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 12px;
                border: 1px solid #777;
                border-radius: 8px;
            }
        """)

        history_title = QLabel("История фаз")
        history_title.setStyleSheet(
            "font-size: 14px; font-weight: bold;"
        )

        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setPlaceholderText(
            "Здесь будут отображаться пройденные фазы"
        )
        self.history.setStyleSheet("""
            QPlainTextEdit {
                font-size: 13px;
                padding: 5px;
                border: 1px solid #777;
                border-radius: 6px;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(self.phase_label)
        layout.addWidget(history_title)
        layout.addWidget(self.history, stretch=1)

    def set_phase(self, phase: str):
        now = time.monotonic()


        if phase == self.current_phase:
            return

        if self.current_phase is not None:
            duration = now - self.phase_start_time

            self.history.appendPlainText(
                f"{self.current_phase} – {duration:.2f} сек."
            )

        self.current_phase = phase
        self.phase_start_time = now

        self.phase_label.setText(phase)

    def reset(self):
        self.current_phase = None
        self.phase_start_time = None
        self.phase_label.setText("Ожидание упражнения")

    def begin_video(self, video_name: str):
        if self.history.toPlainText():
            self.history.appendPlainText("")
            self.history.appendPlainText(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            self.history.appendPlainText("")

        self.history.appendPlainText(f"Видео: {video_name}")
        self.history.appendPlainText("")

        self.current_phase = None
        self.phase_start_time = None
        self.phase_label.setText("Ожидание упражнения")