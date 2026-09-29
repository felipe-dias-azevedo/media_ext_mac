import os
import sys
import shutil
from PyQt6.QtCore import QProcess, QUrl
from PyQt6.QtGui import QDesktopServices


def reveal_in_file_manager(path: str) -> None:
    path = os.path.abspath(path)

    if sys.platform == "darwin":
        QProcess.startDetached("open", ["-R", path])

    elif sys.platform == "win32":
        # Note: "/select," and the path must be ONE argument on Windows
        QProcess.startDetached("explorer.exe", [f"/select,{os.path.normpath(path)}"])

    else:
        # Linux: try the freedesktop FileManager1 D-Bus interface (selects the file)
        if shutil.which("dbus-send"):
            uri = QUrl.fromLocalFile(path).toString()
            ok = QProcess.startDetached("dbus-send", [
                "--session", "--dest=org.freedesktop.FileManager1",
                "--type=method_call", "/org/freedesktop/FileManager1",
                "org.freedesktop.FileManager1.ShowItems",
                f"array:string:{uri}", "string:",
            ])
            if ok:
                return
        # Fallback: just open the containing folder
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))