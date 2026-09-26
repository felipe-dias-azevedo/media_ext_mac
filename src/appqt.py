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
API — NSImage.imageWithSystemSymbolName_). Icons come from qtawesome, which
bundles Font Awesome/Material Design Icons as fonts and renders vector icons
that stay crisp at any size and on HiDPI/Retina screens. Install it with
`pip install qtawesome`.

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
    pip install PyQt6 qtawesome
    python3 media_ext.py
"""

import os
import sys
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from utils.qt_icons import create_symbol
from utils.theme import Theme, get_theme, refresh_theme
from utils.url_validator import YtValidator
from views.url_row import URLRowView

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

# The downloader service is kept as-is and referenced later — see module
# docstring above. This import is left in place on purpose.
from services.downloader import Downloader

_APP_ICON_PATH = Path(__file__).resolve().parent.parent / "icon" / "icon_1024.png"


def _app_icon() -> QIcon:
    return QIcon(str(_APP_ICON_PATH))




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


def _show_about_dialog(window):
    icon = _app_icon()
    dialog = QMessageBox(window)
    dialog.setWindowTitle("About MediaExt")
    dialog.setWindowIcon(icon)
    dialog.setText("MediaExt\nA small media-extraction utility.")
    dialog.setIconPixmap(icon.pixmap(QSize(64, 64)))
    dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
    dialog.exec()


def build_menu_bar(window: QMainWindow):
    menubar = window.menuBar()

    file_menu = menubar.addMenu("&File")

    about_action = QAction("About MediaExt", window)
    about_action.triggered.connect(lambda: _show_about_dialog(window))
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


class DownloaderLogger:
    def __init__(self, handler):
        self.content = ""
        self.handler = handler

    def output(self, text):
        self.content += text + "\n"

        if "--dev" in __import__("sys").argv:
            print(text)

        self.handler(self.content)

    def debug(self, msg):
        self.output(f"{msg}")

    def info(self, msg):
        self.output(f"[INFO] {msg}")

    def warning(self, msg):
        self.output(f"[WARNING] {msg}")

    def error(self, msg):
        self.output(f"[ERROR] {msg}")

    def reset(self):
        self.content = ""


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
    DEFAULT_NORMALIZATION = "High"

    def __init__(self):
        super().__init__()
        self.setWindowIcon(_app_icon())
        self.setWindowTitle("Media.Ext")
        self.resize(840, 620)
        self.setMinimumSize(600, 360)

        self.logger = DownloaderLogger(lambda x: print(x))
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
            self.logger.error(f"Error {type(e).__name__}: {e}")
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
    app.setWindowIcon(_app_icon())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()