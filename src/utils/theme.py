from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication


class Theme:
    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            self.separator = QColor(84, 84, 88, 166)
            self.secondary_text = QColor(235, 235, 245, 153)
            self.fill = QColor(118, 118, 128, 61)
            self.hover_fill = QColor(255, 255, 255, 31)
            self.pressed_fill = QColor(255, 255, 255, 46)
            self.icon_secondary = QColor(152, 152, 157)
            self.success = QColor(48, 209, 88)
            self.error = QColor(255, 69, 58)
        else:
            self.separator = QColor(209, 209, 214)
            self.secondary_text = QColor(74, 74, 80)
            self.fill = QColor(245, 245, 247)
            self.icon_secondary = QColor(110, 110, 115)
            self.hover_fill = QColor(0, 0, 0, 15)
            self.pressed_fill = QColor(0, 0, 0, 26)
            self.success = QColor(52, 199, 89)
            self.error = QColor(255, 59, 48)

    @staticmethod
    def rgba(color: QColor) -> str:
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alphaF():.3f})"


def _detect_dark_mode() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    try:
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return True
        if scheme == Qt.ColorScheme.Light:
            return False
    except Exception:
        pass
    return app.palette().color(app.palette().ColorRole.Window).lightness() < 128


def _theme_instance() -> Theme:
    return Theme(_detect_dark_mode())


_theme_instance: Theme | None = None


def get_theme() -> Theme:
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = Theme(_detect_dark_mode())
    return _theme_instance


def refresh_theme() -> Theme:
    global _theme_instance
    _theme_instance = Theme(_detect_dark_mode())
    return _theme_instance
