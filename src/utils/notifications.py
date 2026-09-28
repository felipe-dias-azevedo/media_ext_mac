from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from utils.qt_icons import app_icon

_tray_icon: QSystemTrayIcon | None = None


def _get_tray_icon() -> QSystemTrayIcon | None:
    global _tray_icon

    application = QApplication.instance()
    if application is None or not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    if _tray_icon is None:
        _tray_icon = QSystemTrayIcon(app_icon(), application)
        _tray_icon.show()

    return _tray_icon


def send_notification(title: str, subtitle: str = "", body: str = "") -> None:
    message = "\n".join(part for part in (subtitle, body) if part)
    tray_icon = _get_tray_icon()
    if tray_icon is not None:
        tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
        )
