
from PyQt6.QtCore import (
    QSize,
    Qt,
)
from PyQt6.QtGui import (
    QFont,
    QGuiApplication,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QWidget,
)
from utils.qt_icons import create_symbol
from utils.theme import Theme, get_theme
from utils.url_validator import YtValidator

class URLRowView(QWidget):

    ACCENT = "#0A84FF"

    def __init__(self, on_extract, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)

        theme = get_theme()

        self.container = QFrame(self)
        self.container.setObjectName("urlContainer")

        self.url_inline_label = QLabel("URL")

        self.url_field = QLineEdit()
        self.url_field.setFrame(False)
        self.url_field.setPlaceholderText("Paste a video link")
        self.url_field.setStyleSheet("background: transparent; border: none;")
        self.url_field.returnPressed.connect(on_extract)

        self.paste_button = QToolButton()
        self.paste_button.setIcon(create_symbol("doc.on.clipboard", theme.icon_secondary))
        self.paste_button.setIconSize(QSize(16, 16))
        self.paste_button.setAutoRaise(True)
        self.paste_button.setToolTip("Paste")
        self.paste_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.paste_button.clicked.connect(self._paste_url)

        row = QHBoxLayout(self.container)
        row.setContentsMargins(10, 0, 10, 0)
        row.setSpacing(10)
        row.addWidget(self.url_inline_label)
        row.addWidget(self.url_field, 1)
        row.addWidget(self.paste_button)

        self.extract_button = QPushButton("Extract")
        self.extract_button.setFixedSize(76, 32)
        self.extract_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.extract_button.setDefault(True)
        self.extract_button.clicked.connect(on_extract)
        extract_font = self.extract_button.font()
        extract_font.setWeight(QFont.Weight.DemiBold)
        self.extract_button.setFont(extract_font)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)
        outer.addWidget(self.container, 1)
        outer.addWidget(self.extract_button, 0)
        self.apply_theme()

    def apply_theme(self):
        theme = get_theme()
        self.container.setStyleSheet(
            "#urlContainer {"
            f"  background-color: {Theme.rgba(theme.fill)};"
            f"  border: 1px solid {Theme.rgba(theme.separator)};"
            "  border-radius: 6px;"
            "}"
        )
        self.url_inline_label.setStyleSheet(
            f"color: {Theme.rgba(theme.secondary_text)}; border: none; background: transparent;"
        )
        self.paste_button.setStyleSheet(
            "QToolButton {"
            "  border: none;"
            "  background: transparent;"
            "  border-radius: 4px;"
            "  padding: 3px;"
            "}"
            f"QToolButton:hover {{ background-color: {Theme.rgba(theme.hover_fill)}; }}"
            f"QToolButton:pressed {{ background-color: {Theme.rgba(theme.pressed_fill)}; }}"
        )
        self.extract_button.setStyleSheet(
            "QPushButton {"
            f"  background-color: {self.ACCENT};"
            "  color: white;"
            "  border: none;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover:!disabled { background-color: #3399FF; }"
            "QPushButton:pressed:!disabled { background-color: #0764C4; }"
            "QPushButton:disabled {"
            f"  background-color: {Theme.rgba(theme.fill)};"
            f"  color: {Theme.rgba(theme.secondary_text)};"
            "}"
        )

    def _paste_url(self):
        text = QGuiApplication.clipboard().text()
        if not text:
            QApplication.beep()
            return
        validator = YtValidator(text)
        if not validator.is_valid_url():
            QApplication.beep()
            return
        self.url_field.setText(text)

    def url_value(self):
        return self.url_field.text()

    def clear_url(self):
        self.url_field.clear()

    def set_enabled(self, enabled):
        self.url_field.setEnabled(enabled)
        self.paste_button.setEnabled(enabled)
        self.extract_button.setEnabled(enabled)

