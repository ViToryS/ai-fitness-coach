
import time

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QTextCharFormat, QTextCursor


class PhasePanel(QWidget):
    """Показывает текущую фазу и историю анализа упражнения."""

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

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setPlaceholderText(
            "Здесь будут отображаться пройденные фазы"
        )
        self.history.setStyleSheet("""
            QTextEdit {
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

    def _append_history_line(self, text: str, color=None):
        cursor = self.history.textCursor()
        cursor.movePosition(QTextCursor.End)

        text_format = QTextCharFormat()
        text_color = (
            QColor(color)
            if color is not None
            else self.history.palette().color(QPalette.Text)
        )
        text_format.setForeground(text_color)

        cursor.insertText(text, text_format)
        cursor.insertBlock()

        self.history.setTextCursor(cursor)
        self.history.ensureCursorVisible()

    def set_phase(self, phase: str):
        now = time.monotonic()

        if phase == self.current_phase:
            return

        if self.current_phase is not None:
            duration = now - self.phase_start_time

            self._append_history_line(
                f"{self.current_phase} – {duration:.2f} сек."
            )

        self.current_phase = phase
        self.phase_start_time = now

        self.phase_label.setText(phase)

    def add_viewpoint(self, viewpoint: str, count: int):
        self._append_history_line(
            f"Ракурс: {viewpoint} ({count})",
            "#3989D6"
        )

    def reset(self):
        self.current_phase = None
        self.phase_start_time = None
        self.phase_label.setText("Ожидание упражнения")

    def begin_video(self, video_name: str):
        if self.history.toPlainText():
            self._append_history_line("")
            self._append_history_line(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            self._append_history_line("")

        self._append_history_line(f"Видео: {video_name}")
        self._append_history_line("")

        self.current_phase = None
        self.phase_start_time = None
        self.phase_label.setText("Ожидание упражнения")
