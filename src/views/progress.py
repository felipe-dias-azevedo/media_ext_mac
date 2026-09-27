from dataclasses import dataclass

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    Qt,
)
from PyQt6.QtGui import (
    QFont,
    QIcon,
    QPainter,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from utils.qt_icons import create_symbol
from utils.theme import Theme, get_theme
from views.current_step_separator_view import CurrentStepSeparator
from views.spinner import SpinnerWidget


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
