from PyQt6.QtCore import (
    QPoint,
    Qt,
    QTimer,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QWidget,
)

from utils.theme import get_theme

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

