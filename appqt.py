#!/usr/bin/env python3
"""
MediaExt — PyQt6 single-file port
==================================

This is a single-file migration of the original PyObjC/AppKit macOS app to
PyQt6. No PyObjC/Cocoa is used anywhere — only PyQt6 and the Python standard
library.

What's included (ported 1:1, just re-platformed):
  - URLRowView            -> URL input row with paste button + Extract button
  - ProgressStepsView /
    StepRowView /
    CurrentStepSeparator  -> animated step list (loading / success / error)
  - url_validator.YtValidator -> unchanged logic, no Cocoa dependency to begin with
  - utils.human_size      -> unchanged, no Cocoa dependency to begin with
  - menu.py                -> simplified QMenuBar (File / Edit / Window / Help)
  - app.py                 -> MainWindow, replacing AppDelegate + RootSplitVC + ContentVC

Deliberately left out (per instructions):
  - History sidebar (SidebarVC) and the "add row to sidebar" step after saving
  - Log viewer window (LogWindowController) — replaced with a plain console
    logger that keeps the same .info()/.warning()/.error()/.reset() interface
  - Settings window (SettingsWindowController) / UserDefaults — replaced with
    a single DEFAULT_NORMALIZATION constant on MainWindow
  - macOS UNUserNotificationCenter notifications

SF Symbols replacement
-----------------------
PyQt has no built-in equivalent of SF Symbols (that was a macOS/AppKit-only
API — NSImage.imageWithSystemSymbolName_). Icons here come from qtawesome
(pip install qtawesome), which bundles Font Awesome/Material Design Icons as
fonts and renders them through its own QIconEngine — vector, so they stay
crisp at any size and on HiDPI/Retina screens, and tintable via `color=`
the same way NSImage.contentTintColor was used. If qtawesome isn't
installed, create_symbol() automatically falls back to a small hand-drawn
QIconEngine (see SymbolIconEngine) so the app still runs with just PyQt6 —
that fallback also paints live at whatever size Qt requests rather than
baking one fixed-size QPixmap, so it doesn't go blurry on HiDPI either.

Dark/light mode
----------------
Borders, separators, and secondary text use an explicit `Theme` (see below)
carrying the same dynamic colors AppKit was using — separatorColor,
secondaryLabelColor, tertiarySystemFillColor, systemGreen/RedColor — with
real light/dark RGBA values, rather than generic QSS palette roles like
`palette(mid)` (meant for 3D widget shading, not for this) which read as
low-contrast/wrong in dark mode.

The Downloader service (services/downloader.py) is intentionally NOT
migrated or touched — the calls into it (`Downloader(logger, progresser)`,
`.download(url, normalization=...)`, `.move_file(src, dst)`, `.fetch(url)`)
are kept exactly as they were. Drop your existing `services/downloader.py`
(as a `services` package, i.e. `services/__init__.py` + `services/downloader.py`)
next to this file and it will be picked up unchanged.

Run:
    pip install PyQt6 qtawesome   # qtawesome is optional but recommended
    python3 media_ext.py
"""

import math
import os
import sys
import threading
from dataclasses import dataclass
from enum import Enum
from re import compile as re_compile
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QIconEngine,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# The downloader service is kept as-is and referenced later — see module
# docstring above. This import is left in place on purpose.
from downloader import Downloader


# ============================================================
# Symbols (SF Symbols replacement)
#
# PyQt has no built-in SF Symbols equivalent, so real vector icons come from
# qtawesome (bundles Font Awesome / Material Design Icons as fonts, renders
# crisply at any size/DPI via its own QIconEngine — pip install qtawesome).
# If qtawesome isn't installed, create_symbol() falls back to a hand-drawn
# QIconEngine below, so the app still runs with just PyQt6. The fallback
# paints live at whatever size Qt actually requests (rather than baking one
# fixed-size QPixmap), so it stays sharp on HiDPI/Retina screens too — a
# baked small QPixmap stretched onto a HiDPI screen is what made the first
# pass look blurry.
# ============================================================

try:
    import qtawesome as qta
    _HAS_QTA = True
except ImportError:  # qtawesome is optional; hand-drawn fallback covers this
    qta = None
    _HAS_QTA = False

# Maps our semantic symbol names (matching the old SF Symbol names) to
# Font Awesome 5 Solid glyph names.
_QTA_NAMES = {
    "checkmark.circle.fill": "fa5s.check-circle",
    "xmark.circle.fill": "fa5s.times-circle",
    "doc.on.clipboard": "fa5s.paste",
    "gearshape": "fa5s.cog",
    "chevron.down": "fa5s.chevron-down",
}


def _paint_checkmark_circle_fill(p: QPainter, rect: QRectF, color: QColor):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawEllipse(rect)

    w = rect.width()
    pen = QPen(QColor("white"))
    pen.setWidthF(max(1.4, w * 0.12))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)

    path = QPainterPath()
    path.moveTo(rect.left() + w * 0.27, rect.top() + w * 0.52)
    path.lineTo(rect.left() + w * 0.44, rect.top() + w * 0.68)
    path.lineTo(rect.left() + w * 0.75, rect.top() + w * 0.32)
    p.drawPath(path)


def _paint_xmark_circle_fill(p: QPainter, rect: QRectF, color: QColor):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawEllipse(rect)

    w = rect.width()
    pen = QPen(QColor("white"))
    pen.setWidthF(max(1.4, w * 0.12))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)

    m = w * 0.30
    p.drawLine(QPoint(int(rect.left() + m), int(rect.top() + m)), QPoint(int(rect.right() - m), int(rect.bottom() - m)))
    p.drawLine(QPoint(int(rect.right() - m), int(rect.top() + m)), QPoint(int(rect.left() + m), int(rect.bottom() - m)))


def _paint_doc_on_clipboard(p: QPainter, rect: QRectF, color: QColor):
    w, h = rect.width(), rect.height()
    pen = QPen(color)
    pen.setWidthF(max(1.3, w * 0.09))
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    back = QRectF(rect.left() + w * 0.32, rect.top() + h * 0.08, w * 0.54, h * 0.62)
    p.drawRoundedRect(back, w * 0.05, w * 0.05)

    body = QRectF(rect.left() + w * 0.14, rect.top() + h * 0.30, w * 0.58, h * 0.62)
    p.drawRoundedRect(body, w * 0.06, w * 0.06)

    clip = QRectF(rect.left() + w * 0.30, rect.top() + h * 0.20, w * 0.24, h * 0.13)
    p.setBrush(QBrush(color))
    p.drawRoundedRect(clip, w * 0.03, w * 0.03)


def _paint_gearshape(p: QPainter, rect: QRectF, color: QColor):
    cx, cy = rect.center().x(), rect.center().y()
    r_outer = rect.width() * 0.46
    r_inner = rect.width() * 0.19
    teeth = 8

    path = QPainterPath()
    for i in range(teeth * 2):
        ang = math.pi * i / teeth
        r = r_outer if i % 2 == 0 else r_outer * 0.78
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    path.closeSubpath()

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawPath(path)

    # Punch the center hole out to transparent.
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    p.setBrush(QBrush(QColor(0, 0, 0, 255)))
    p.drawEllipse(QRectF(cx - r_inner, cy - r_inner, r_inner * 2, r_inner * 2))
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)


def _paint_chevron_down(p: QPainter, rect: QRectF, color: QColor):
    w = rect.width()
    pen = QPen(color)
    pen.setWidthF(max(1.5, w * 0.14))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)

    path = QPainterPath()
    path.moveTo(rect.left() + w * 0.22, rect.top() + w * 0.36)
    path.lineTo(rect.center().x(), rect.top() + w * 0.64)
    path.lineTo(rect.right() - w * 0.22, rect.top() + w * 0.36)
    p.drawPath(path)


class SymbolIconEngine(QIconEngine):
    """Resolution-independent fallback icon engine: paints live into
    whatever rect/QPainter Qt hands it (correct DPI every time), instead of
    baking a single fixed-size QPixmap up front. Only used when qtawesome
    isn't installed."""

    _PAINTERS = {
        "checkmark.circle.fill": _paint_checkmark_circle_fill,
        "xmark.circle.fill": _paint_xmark_circle_fill,
        "doc.on.clipboard": _paint_doc_on_clipboard,
        "gearshape": _paint_gearshape,
        "chevron.down": _paint_chevron_down,
    }

    def __init__(self, name: str, color: QColor):
        super().__init__()
        self._name = name
        self._color = QColor(color)

    def paint(self, painter: QPainter, rect, mode, state):
        color = QColor(self._color)
        if mode == QIcon.Mode.Disabled:
            color.setAlpha(color.alpha() // 2)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(rect).adjusted(1, 1, -1, -1)
        paint_fn = self._PAINTERS.get(self._name)
        if paint_fn is not None:
            paint_fn(painter, r, color)
        else:
            # Unknown symbol name: a plain dot rather than a crash.
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(r.adjusted(r.width() * 0.3, r.height() * 0.3, -r.width() * 0.3, -r.height() * 0.3))
        painter.restore()

    def pixmap(self, size: QSize, mode, state) -> QPixmap:
        pm = QPixmap(size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        self.paint(painter, pm.rect(), mode, state)
        painter.end()
        return pm

    def clone(self) -> "SymbolIconEngine":
        return SymbolIconEngine(self._name, self._color)


_symbol_icon_cache: dict = {}


def create_symbol(name: str, color: "QColor | None" = None) -> QIcon:
    """Returns a resolution-independent QIcon for one of this app's symbol
    names. Prefers qtawesome (crisp Font Awesome glyphs); falls back to the
    hand-drawn QIconEngine above if qtawesome isn't installed."""
    color = QColor(color) if color is not None else QColor(142, 142, 147)
    cache_key = (name, color.name(QColor.NameFormat.HexArgb))
    cached = _symbol_icon_cache.get(cache_key)
    if cached is not None:
        return cached

    icon = None
    if _HAS_QTA and name in _QTA_NAMES:
        try:
            icon = qta.icon(_QTA_NAMES[name], color=color)
        except Exception:
            icon = None  # fall through to hand-drawn engine below

    if icon is None:
        icon = QIcon(SymbolIconEngine(name, color))

    _symbol_icon_cache[cache_key] = icon
    return icon


# ============================================================
# Theme colors (light/dark mode)
#
# The first pass used QSS roles like `palette(mid)` for borders and
# secondary text. Those roles exist for widget 3D shading, not for the
# label/separator/fill semantics this app actually wants, so they read as
# "wrong" in dark mode (too dark to see, wrong tint, etc). This uses the
# same dynamic colors AppKit was using — NSColor.separatorColor,
# secondaryLabelColor, tertiarySystemFillColor, systemGreen/RedColor — with
# their actual light/dark RGBA values, picked explicitly based on the
# active color scheme.
# ============================================================

class Theme:
    def __init__(self, dark: bool):
        self.dark = dark
        if dark:
            self.separator = QColor(84, 84, 88, 166)         # separatorColor (dark)
            self.secondary_text = QColor(235, 235, 245, 153)  # secondaryLabelColor (dark)
            self.fill = QColor(118, 118, 128, 61)              # tertiarySystemFillColor (dark)
            self.hover_fill = QColor(255, 255, 255, 31)
            self.pressed_fill = QColor(255, 255, 255, 46)
            self.icon_secondary = QColor(152, 152, 157)
            self.success = QColor(48, 209, 88)                 # systemGreenColor (dark)
            self.error = QColor(255, 69, 58)                   # systemRedColor (dark)
        else:
            self.separator = QColor(209, 209, 214)
            self.secondary_text = QColor(74, 74, 80)
            self.fill = QColor(245, 245, 247)
            self.icon_secondary = QColor(110, 110, 115)
            # self.separator = QColor(60, 60, 67, 74)           # separatorColor (light)
            # self.secondary_text = QColor(60, 60, 67, 153)     # secondaryLabelColor (light)
            # self.fill = QColor(118, 118, 128, 31)              # tertiarySystemFillColor (light)
            self.hover_fill = QColor(0, 0, 0, 15)
            self.pressed_fill = QColor(0, 0, 0, 26)
            # self.icon_secondary = QColor(142, 142, 147)
            self.success = QColor(52, 199, 89)                 # systemGreenColor (light)
            self.error = QColor(255, 59, 48)                   # systemRedColor (light)

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
    # Older Qt without colorScheme(): infer from the window background.
    return app.palette().color(QPalette.ColorRole.Window).lightness() < 128


_theme_instance: "Theme | None" = None


def get_theme() -> Theme:
    """Lazily computed, cached for the process lifetime. Call refresh_theme()
    if you need to react to a live OS theme switch."""
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = Theme(_detect_dark_mode())
    return _theme_instance


def refresh_theme() -> Theme:
    global _theme_instance
    _theme_instance = Theme(_detect_dark_mode())
    return _theme_instance


# ============================================================
# Spinner (NSProgressIndicatorStyleSpinning replacement)
# ============================================================

class SpinnerWidget(QWidget):
    """Small indeterminate spinner drawn with QPainter."""

    def __init__(self, diameter: int = 16, parent=None):
        super().__init__(parent)
        self._diameter = diameter
        self._angle = 0
        self.setFixedSize(diameter, diameter)

        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)

        self.hide()

    def _tick(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def start(self):
        self.show()
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.hide()

    def paintEvent(self, event):  # noqa: N802 (Qt override)
        if not self.isVisible():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)

        base = get_theme().icon_secondary
        blades = 8
        r = self._diameter / 2 - 1
        for i in range(blades):
            painter.save()
            painter.rotate(360 / blades * i)
            alpha = int(255 * (i + 1) / blades)
            pen = QPen(QColor(base.red(), base.green(), base.blue(), alpha))
            pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPoint(0, int(r * 0.45)), QPoint(0, int(r)))
            painter.restore()
        painter.end()


# ============================================================
# Progress steps (progress.py port)
# ============================================================

@dataclass
class ProgressStep:
    title: str
    description: str | None = None
    icon: str | None = None
    loading: bool = False
    success: bool | None = None


class IconView(QWidget):
    """Paints a QIcon live into its own rect on every paintEvent, instead of
    baking one fixed-resolution QPixmap. Qt supplies the correctly scaled
    QPainter for the current screen, so this stays crisp on HiDPI/Retina —
    unlike a QLabel.setPixmap() with a pre-rendered small pixmap."""

    def __init__(self, size: int = 18, parent=None):
        super().__init__(parent)
        self._icon: "QIcon | None" = None
        self.setFixedSize(size, size)

    def set_icon(self, icon: QIcon):
        self._icon = icon
        self.update()

    def paintEvent(self, event):  # noqa: N802 (Qt override)
        if self._icon is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._icon.paint(painter, self.rect())
        painter.end()


class StepRowView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.icon_view = IconView(18)

        self.spinner = SpinnerWidget(16)

        self.leading = QWidget()
        self.leading.setFixedSize(18, 18)
        leading_stack = QStackedLayout(self.leading)
        leading_stack.setContentsMargins(0, 0, 0, 0)
        leading_stack.addWidget(self.icon_view)
        leading_stack.addWidget(self.spinner)
        self._leading_stack = leading_stack

        self.title_label = QLabel()
        title_font = self.title_label.font()
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(title_font)

        self._symbol_name = None
        self.description_label = QLabel()
        desc_font = self.description_label.font()
        desc_font.setPointSize(max(desc_font.pointSize() - 1, 9))
        self.description_label.setFont(desc_font)
        self.description_label.hide()

        text_stack = QVBoxLayout()
        text_stack.setSpacing(2)
        text_stack.setContentsMargins(0, 0, 0, 0)
        text_stack.addWidget(self.title_label)
        text_stack.addWidget(self.description_label)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addWidget(self.leading, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(text_stack, 1)

        self.leading.hide()
        self.apply_theme()

    def apply_theme(self):
        theme = get_theme()
        self.description_label.setStyleSheet(f"color: {Theme.rgba(theme.secondary_text)};")
        if self._symbol_name:
            if self._symbol_name == "checkmark.circle.fill":
                color = theme.success
            elif self._symbol_name == "xmark.circle.fill":
                color = theme.error
            else:
                color = theme.icon_secondary
            self.icon_view.set_icon(create_symbol(self._symbol_name, color))

    # ----- state -----

    def set_title_description(self, title, description=None):
        self.title_label.setText(title)
        if description:
            self.description_label.setText(str(description))
            self.description_label.show()
        else:
            self.description_label.clear()
            self.description_label.hide()

    def set_icon(self, symbol_name, color=None):
        self.spinner.stop()
        self.leading.show()
        self._symbol_name = symbol_name
        if color is None:
            color = get_theme().icon_secondary
        self.icon_view.set_icon(create_symbol(symbol_name, color))
        self._leading_stack.setCurrentWidget(self.icon_view)

    def set_loading(self):
        self.leading.show()
        self._leading_stack.setCurrentWidget(self.spinner)
        self.spinner.start()

    def set_success(self):
        self.set_icon("checkmark.circle.fill", get_theme().success)

    def set_error(self):
        self.set_icon("xmark.circle.fill", get_theme().error)


class CurrentStepSeparator(QFrame):
    """1px hairline row separator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(f"background-color: {Theme.rgba(get_theme().separator)}; border: none;")


class ProgressStepsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_row = None
        self._rows = []

        self.background = QFrame(self)
        self.background.setObjectName("progressBackground")

        self.stack_layout = QVBoxLayout(self.background)
        self.stack_layout.setContentsMargins(10, 10, 10, 10)
        self.stack_layout.setSpacing(10)
        self.stack_layout.addStretch(1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.background)
        self.apply_theme()

    def apply_theme(self):
        theme = get_theme()
        self.background.setStyleSheet(
            "#progressBackground {"
            f"  background-color: {Theme.rgba(theme.fill)};"
            f"  border: 1px solid {Theme.rgba(theme.separator)};"
            "  border-radius: 8px;"
            "}"
        )
        for item in self._rows:
            if isinstance(item, (StepRowView, CurrentStepSeparator)):
                item.apply_theme()

    # ----- internal -----

    def _append_row_with_separator(self, row):
        self.stack_layout.takeAt(self.stack_layout.count() - 1)  # drop trailing stretch
        if self._rows:
            separator = CurrentStepSeparator()
            self.stack_layout.addWidget(separator)
            self._rows.append(separator)
        self.stack_layout.addWidget(row)
        self._rows.append(row)
        self.stack_layout.addStretch(1)
        self._animate_insertion(row)

    def _animate_insertion(self, row):
        row.setMaximumHeight(0)
        effect = QGraphicsOpacityEffect(row)
        effect.setOpacity(0.0)
        row.setGraphicsEffect(effect)
        row.adjustSize()
        target_height = row.sizeHint().height()

        fade = QPropertyAnimation(effect, b"opacity", row)
        fade.setDuration(200)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)

        grow = QPropertyAnimation(row, b"maximumHeight", row)
        grow.setDuration(200)
        grow.setStartValue(0)
        grow.setEndValue(target_height)
        grow.setEasingCurve(QEasingCurve.Type.OutCubic)
        grow.finished.connect(lambda: row.setMaximumHeight(16777215))

        group = QParallelAnimationGroup(row)
        group.addAnimation(fade)
        group.addAnimation(grow)
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        row._insert_anim = group  # keep a reference alive until it finishes

    # ----- public API (progress.py port) -----

    def add_step(self, title, description=None, icon=None):
        row = StepRowView()
        row.set_title_description(title, description)
        if icon:
            row.set_icon(icon)
        self._append_row_with_separator(row)
        return row

    def begin_current_step(self, title, description=None, icon=None):
        self.current_row = StepRowView()
        self.current_row.set_title_description(title, description)
        if icon:
            self.current_row.set_icon(icon)
        self.current_row.set_loading()
        self._append_row_with_separator(self.current_row)

    def update_current_step(self, title=None, description=None):
        if not self.current_row:
            return
        if title is not None:
            self.current_row.title_label.setText(title)
        if description is not None:
            self.current_row.set_title_description(self.current_row.title_label.text(), description)

    def finish_current_step_success(self, title, description=None):
        if not self.current_row:
            return
        self.current_row.set_title_description(title, description)
        self.current_row.set_success()
        self.current_row = None

    def finish_current_step_error(self, title, description=None):
        if not self.current_row:
            return
        self.current_row.set_title_description(title, description)
        self.current_row.set_error()
        self.current_row = None

    def reset(self):
        while self.stack_layout.count():
            item = self.stack_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows = []
        self.stack_layout.addStretch(1)
        self.current_row = None


# ============================================================
# URL validator (url_validator.py — unchanged, no Cocoa dependency)
# ============================================================

class YtValidator:

    _URL_RE = re_compile(r"^(https?://)?(([a-zA-Z0-9-]+\.)?youtube\.com|youtu\.be)/.+$")

    def __init__(self, url: str):
        self.url = url
        self.query = parse_qs(urlparse(url).query)

    def is_valid_url(self):
        return bool(self._URL_RE.match(self.url))

    def is_playlist(self):
        return "list" in self.query

    def is_content(self):
        return "v" in self.query

    @staticmethod
    def remove_playlist_from_query(url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query.pop("list", None)
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))


# ============================================================
# utils.py — unchanged
# ============================================================

def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1000:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1000


# ============================================================
# URL row (url_row.py port)
# ============================================================

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


# ============================================================
# Menu bar (menu.py port — simplified: no Preferences/Logs/Sidebar)
# ============================================================

def _focused_widget_action(window, text, shortcut, method_name):
    action = QAction(text, window)
    action.setShortcut(QKeySequence(shortcut))

    def _trigger():
        widget = QApplication.focusWidget()
        if widget is not None and hasattr(widget, method_name):
            getattr(widget, method_name)()

    action.triggered.connect(_trigger)
    return action


def build_menu_bar(window: QMainWindow):
    menubar = window.menuBar()

    file_menu = menubar.addMenu("&File")

    about_action = QAction("About MediaExt", window)
    about_action.triggered.connect(
        lambda: QMessageBox.about(window, "About MediaExt", "MediaExt\nA small media-extraction utility.")
    )
    file_menu.addAction(about_action)
    file_menu.addSeparator()

    close_action = QAction("Close Window", window)
    close_action.setShortcut(QKeySequence("Ctrl+W"))
    close_action.triggered.connect(window.close)
    file_menu.addAction(close_action)

    file_menu.addSeparator()

    quit_action = QAction("Quit MediaExt", window)
    quit_action.setShortcut(QKeySequence("Ctrl+Q"))
    quit_action.triggered.connect(QApplication.instance().quit)
    file_menu.addAction(quit_action)

    edit_menu = menubar.addMenu("&Edit")
    edit_menu.addAction(_focused_widget_action(window, "Cut", "Ctrl+X", "cut"))
    edit_menu.addAction(_focused_widget_action(window, "Copy", "Ctrl+C", "copy"))
    edit_menu.addAction(_focused_widget_action(window, "Paste", "Ctrl+V", "paste"))
    edit_menu.addAction(_focused_widget_action(window, "Select All", "Ctrl+A", "selectAll"))

    window_menu = menubar.addMenu("&Window")
    minimize_action = QAction("Minimize", window)
    minimize_action.setShortcut(QKeySequence("Ctrl+M"))
    minimize_action.triggered.connect(window.showMinimized)
    window_menu.addAction(minimize_action)

    zoom_action = QAction("Zoom", window)
    zoom_action.triggered.connect(
        lambda: window.showNormal() if window.isMaximized() else window.showMaximized()
    )
    window_menu.addAction(zoom_action)

    help_menu = menubar.addMenu("&Help")
    help_menu.addAction(QAction("MediaExt Help", window))  # no-op, matches original


# ============================================================
# Progress plumbing (app.py: Progresser / ProgressStatus port)
# ============================================================

class ProgressStatus(Enum):
    ADD = 0
    BEGIN = 1
    UPDATE = 2
    SUCCESS = 3
    ERROR = 4


class Progresser:
    """Bridges the (unchanged) Downloader service's callbacks into the UI.
    Downloader calls these from a background thread; `handler` is expected
    to marshal onto the GUI thread — see WorkerSignals below."""

    def __init__(self, handler):
        self.handler = handler
        self.downloading = False
        self.postprocessing = False

    def download(self, msg):
        self.downloading = True
        self.handler((ProgressStatus.UPDATE, "Downloading", msg, None))

    def finish_download(self, msg):
        self.downloading = False
        self.handler((ProgressStatus.SUCCESS, "Download Completed", msg, None))

    def postprocess(self, msg):
        self.postprocessing = True
        self.handler((ProgressStatus.BEGIN, "Post Processing", msg, None))

    def finish_postprocess(self, msg):
        self.postprocessing = False
        self.handler((ProgressStatus.SUCCESS, "Post Processing Completed", msg, None))


class ConsoleLogger:
    """Stand-in for the old LogWindowController-backed logger (log viewer
    window is out of scope for this port). Keeps the same interface
    (.reset/.info/.warning/.error) so the downloader service doesn't need
    to change."""

    def reset(self):
        pass

    def info(self, msg):
        print(f"[INFO] {msg}")

    def warning(self, msg):
        print(f"[WARN] {msg}")

    def error(self, msg):
        print(f"[ERROR] {msg}")


class WorkerSignals(QObject):
    """performSelectorOnMainThread_withObject_waitUntilDone_ replacement:
    Qt signals are automatically queued back to the GUI thread when emitted
    from a background thread."""

    progress = pyqtSignal(object)   # (ProgressStatus, title, description, icon)
    extract_finished = pyqtSignal(str)  # src_path
    busy = pyqtSignal(bool)


# ============================================================
# Main window (app.py: AppDelegate + RootSplitVC + ContentVC port)
# ============================================================

class MainWindow(QMainWindow):

    # Settings window / UserDefaults are out of scope for this port.
    DEFAULT_NORMALIZATION = "none"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media.Ext")
        self.resize(840, 620)
        self.setMinimumSize(600, 360)

        self.logger = ConsoleLogger()
        self.signals = WorkerSignals()
        self.progresser = Progresser(self.signals.progress.emit)
        self.downloader = Downloader(self.logger, self.progresser)

        self.signals.progress.connect(self._update_progress)
        self.signals.extract_finished.connect(self._finish_extract)
        self.signals.busy.connect(self.set_busy)

        self.url_row = URLRowView(self._extract)
        self.progress_steps = ProgressStepsView()
        self.progress_steps.hide()

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(self.progress_steps)
        scroll_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(scroll_content)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(self.url_row)
        layout.addWidget(scroll, 1)
        self.setCentralWidget(central)

        build_menu_bar(self)
        app = QApplication.instance()
        style_hints = app.styleHints()
        if hasattr(style_hints, "colorSchemeChanged"):
            style_hints.colorSchemeChanged.connect(self._refresh_theme)
        if hasattr(app, "paletteChanged"):
            app.paletteChanged.connect(self._refresh_theme)

    def _refresh_theme(self, *_):
        previous_dark = get_theme().dark
        theme = refresh_theme()
        if theme.dark == previous_dark:
            return
        self.url_row.apply_theme()
        self.progress_steps.apply_theme()

    # ----- extract flow -----

    def _extract(self):
        text = self.url_row.url_value().strip()
        if not text:
            QApplication.beep()
            return

        validator = YtValidator(text)

        if not validator.is_valid_url():
            QApplication.beep()
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL.")
            return

        if validator.is_content() and validator.is_playlist():
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle("Playlist Detected")
            box.setText(
                "This URL contains a playlist. Would you like to download the "
                "entire playlist or only the current media?"
            )
            current_btn = box.addButton("Current Media", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is not current_btn:
                return
            text = YtValidator.remove_playlist_from_query(text)
            self._start_extract()
            threading.Thread(target=self._download_thread, args=(text,), daemon=True).start()
            return

        if validator.is_playlist():
            # Full playlist item picker was out of scope for this port; the
            # downloader.fetch() hook is kept so it can be wired up later.
            self.logger.info("Playlist URL detected.")
            self.downloader.fetch(text)
            QMessageBox.information(self, "Playlist", "Playlist downloading isn't wired up in this build yet.")
            return

        self._start_extract()
        threading.Thread(target=self._download_thread, args=(text,), daemon=True).start()

    def _start_extract(self):
        self.progress_steps.show()
        self.progress_steps.reset()
        self.logger.reset()
        self.logger.info("Extract started.")
        self.set_busy(True)

    def _download_thread(self, url):
        try:
            normalization = self.DEFAULT_NORMALIZATION
            normalization_text = f"Using normalization: {normalization}"
            self.logger.info(normalization_text)
            self.signals.progress.emit((ProgressStatus.ADD, "Normalization", normalization_text, "gearshape"))

            self.signals.progress.emit((ProgressStatus.BEGIN, "Downloading", "Starting Download...", None))
            path = self.downloader.download(url, normalization=normalization)
            self.logger.info(f"Download finished successfully: {path}")

            self.signals.extract_finished.emit(path)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.signals.progress.emit((ProgressStatus.ERROR, "Error", str(e), None))
            self.signals.busy.emit(False)

    def _update_progress(self, args):
        status, title, description, icon = args
        if status == ProgressStatus.ADD:
            self.progress_steps.add_step(title, description, icon)
        elif status == ProgressStatus.BEGIN:
            self.progress_steps.begin_current_step(title, description, None)
        elif status == ProgressStatus.UPDATE:
            self.progress_steps.update_current_step(title, description)
        elif status == ProgressStatus.SUCCESS:
            self.progress_steps.finish_current_step_success(title, description)
        elif status == ProgressStatus.ERROR:
            self.progress_steps.finish_current_step_error(title, description)

    def _finish_extract(self, src_path):
        try:
            self.progress_steps.begin_current_step("Saving File", "Choose where to save...")
            save_path = self._present_save_panel(src_path)

            if save_path is None:
                self.logger.warning("Save cancelled by user.")
                self.progress_steps.finish_current_step_error("Save Failed", "Cancelled by user.")
                return

            self.progress_steps.finish_current_step_success(
                "Save File Completed", "File: " + os.path.basename(save_path)
            )
            # History sidebar is out of scope for this port; this is where
            # sidebarVC.addRowToSidebar_(media_item) used to be called.
        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            self.progress_steps.finish_current_step_error("Save Failed", str(e))
        finally:
            self.set_busy(False)

    def _present_save_panel(self, src_path):
        suggested = os.path.basename(src_path)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", suggested, "MP3 Audio (*.mp3)")
        if not save_path:
            return None
        self.logger.info(f"Saving to: {save_path}")
        self.downloader.move_file(src_path, save_path)
        self.logger.info("File saved successfully.")
        return save_path

    def set_busy(self, is_busy):
        self.url_row.set_enabled(not is_busy)
        if not is_busy:
            self.url_row.clear_url()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MediaExt")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()