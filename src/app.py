import os
import sys
import threading
from enum import Enum
from utils.theme import get_theme, refresh_theme
from utils.url_validator import YtValidator
from views.menu import build_menu_bar
from views.progress import ProgressStepsView
from views.url_row import URLRowView
from views.log_window import LogWindow
from views.settings import SettingsWindow
from utils.user_defaults import UserDefaults
from utils.notifications import send_notification

from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# The downloader service is kept as-is and referenced later — see module
# docstring above. This import is left in place on purpose.
from services.downloader import Downloader

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
    log_updated = pyqtSignal(str)
    notification = pyqtSignal(str, str)


# ============================================================
# Main window (app.py: AppDelegate + RootSplitVC + ContentVC port)
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # self.setWindowIcon(app_icon()) TODO: check if on windows this is still necessary considering build embeds .ico
        self.setWindowTitle("Media.Ext")
        self.resize(840, 620)
        self.setMinimumSize(600, 360)

        self.log_window = LogWindow(self)
        self.user_defaults = UserDefaults()
        self.settings_window = SettingsWindow(self.user_defaults, self)
        self.signals = WorkerSignals()
        self.signals.log_updated.connect(self.log_window.set_logs)
        self.logger = DownloaderLogger(self.signals.log_updated.emit)
        self.progresser = Progresser(self.signals.progress.emit)
        self.downloader = Downloader(self.logger, self.progresser)

        self.signals.progress.connect(self._update_progress)
        self.signals.extract_finished.connect(self._finish_extract)
        self.signals.busy.connect(self.set_busy)
        self.signals.notification.connect(send_notification)

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

    def show_logs(self):
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def show_preferences(self):
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

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

            """OLD TODO:
            # TODO: present a NSView inside a Sheet for window to choose which items from playlist to download
                    
            # TODO: call self.downloader.download (passing the multiple urls aggregated in a list from info dict)
            # TODO: understand if gonna keep using ProgressSteps
            # TODO: Update workflows to accept the finish of multiple files
            """
            

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
            normalization = self.user_defaults.getNormalization()
            normalization_text = f"Using normalization: {normalization}"
            self.logger.info(normalization_text)
            self.signals.progress.emit((ProgressStatus.ADD, "Normalization", normalization_text, "gearshape"))

            self.signals.progress.emit((ProgressStatus.BEGIN, "Downloading", "Starting Download...", None))
            path = self.downloader.download(url, normalization=normalization)
            self.logger.info(f"Download finished successfully: {path}")
            self.signals.notification.emit("Download Completed", os.path.basename(path))

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()