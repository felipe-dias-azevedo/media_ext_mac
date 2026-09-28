
from PyQt6.QtWidgets import (
    QFrame,
)

from utils.theme import Theme, get_theme

class CurrentStepSeparator(QFrame):
    """1px hairline row separator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(f"background-color: {Theme.rgba(get_theme().separator)}; border: none;")