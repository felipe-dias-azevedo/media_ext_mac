from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QDialog, QFormLayout

from utils.user_defaults import NORMALIZATION_OPTIONS, UserDefaults


class SettingsWindow(QDialog):
    def __init__(self, user_defaults: UserDefaults, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.user_defaults = user_defaults
        self.setWindowTitle("Preferences")
        self.resize(400, 180)
        self.setMinimumSize(360, 140)

        self.normalization_combo = QComboBox(self)
        self.normalization_combo.addItems(
            [option.value for option in NORMALIZATION_OPTIONS]
        )
        self.normalization_combo.setCurrentText(user_defaults.getNormalization())
        self.normalization_combo.currentTextChanged.connect(
            user_defaults.setNormalization
        )

        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addRow("Normalization frequency:", self.normalization_combo)