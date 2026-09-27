
from PyQt6.QtCore import (
    QSize,
)
from PyQt6.QtGui import (
    QAction,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
)
from utils.qt_icons import app_icon

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
    icon = app_icon()
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

    logs_action = QAction("Logs", window)
    logs_action.setShortcut(QKeySequence("Ctrl+L"))
    logs_action.triggered.connect(window.show_logs)
    window_menu.addAction(logs_action)
    window_menu.addSeparator()

    help_menu = menubar.addMenu("&Help")
    help_menu.addAction(QAction("MediaExt Help", window))  # no-op, matches original

