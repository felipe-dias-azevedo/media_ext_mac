from PyQt6.QtGui import QFontDatabase, QTextCursor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QPlainTextEdit


# TODO: check to replace something similar to a NSPanel


class LogWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowTitle("Logs")
        self.resize(540, 420)
        self.setMinimumSize(320, 210)

        self.log_view = QPlainTextEdit(self)
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.log_view.document().setDocumentMargin(10.0)
        self.setCentralWidget(self.log_view)

    def set_logs(self, text):
        self.log_view.setPlainText(text)
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)