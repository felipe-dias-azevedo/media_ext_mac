from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication


class Theme:
    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            self.accent          = QColor(10, 132, 255)           # systemBlue (macOS dark)
            self.separator = QColor(255, 255, 255, 25)   # separatorColor, ~10% white
            self.border    = QColor(255, 255, 255, 38)   # control/field outline, ~15% white
            self.secondary_text  = QColor(235, 235, 245, 153)   # secondaryLabelColor
            self.fill            = QColor(118, 118, 128, 61)    # tertiarySystemFill
            self.hover_fill      = QColor(255, 255, 255, 31)    # ~12% white
            self.pressed_fill    = QColor(255, 255, 255, 46)    # ~18% white
            self.icon_secondary  = QColor(152, 152, 157)        # systemGray (macOS dark)
            self.success         = QColor(50, 215, 75)          # systemGreen (macOS dark)
            self.error           = QColor(255, 69, 58)          # systemRed (dark)
        else:
            self.accent          = QColor(0, 122, 255)            # systemBlue (macOS light)
            self.separator = QColor(0, 0, 0, 25)         # separatorColor, ~10% black
            self.border    = QColor(0, 0, 0, 38)         # control/field outline, ~15% black
            self.secondary_text  = QColor(60, 60, 67, 153)      # secondaryLabelColor
            self.fill            = QColor(118, 118, 128, 31)    # tertiarySystemFill
            self.hover_fill      = QColor(0, 0, 0, 15)          # ~6% black
            self.pressed_fill    = QColor(0, 0, 0, 26)          # ~10% black
            self.icon_secondary  = QColor(142, 142, 147)        # systemGray (light)
            self.success         = QColor(40, 205, 65)          # systemGreen (macOS light)
            self.error           = QColor(255, 59, 48)          # systemRed (light)

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
