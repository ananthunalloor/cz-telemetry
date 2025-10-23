from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QWidget
from collections import deque
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTextEdit


class LogViewer:
    def __init__(self, max_lines=1000) -> None:
        self.max_lines = max_lines
        self.lines = deque(maxlen=self.max_lines)
        self.parent = QWidget()
        self.text = QTextEdit()

    def setup_log_viewer(self) -> QWidget:
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.text.setReadOnly(True)
        mono = QFont("Courier New")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(10)
        self.text.setFont(mono)
        # Optional: disable editing interactions other than selection/copy
        self.text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        layout.addWidget(self.text)
        self.parent.setLayout(layout)

        return self.parent

    def add_log(self, message: str):
        self.lines.appendleft(message)
        self.text.setPlainText("\n".join(self.lines))

        sb = self.text.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.minimum())
