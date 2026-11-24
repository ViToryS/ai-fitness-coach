
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QToolButton,
    QLabel,
)
from PySide6.QtCore import Qt


class PhasePanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QToolButton()
        self.toggle_button.setText("Фаза упражнения")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )

        self.phase_label = QLabel("Ожидание упражнения")
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 12px;"
        )

        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.phase_label)

        self.content.setVisible(False)

        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content)

        self.toggle_button.toggled.connect(self.toggle_content)

    def toggle_content(self, checked):
        self.content.setVisible(checked)
        self.toggle_button.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )

    def set_phase(self, phase: str):
        self.phase_label.setText(phase)

    def reset(self):
        self.set_phase("Ожидание упражнения")
