"""Real-time log output widget."""
from __future__ import annotations
from PySide6.QtWidgets import QPlainTextEdit, QWidget
from PySide6.QtCore import Qt


class LogViewer(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(500)
        self.setMinimumHeight(120)
        self.setPlaceholderText("Output will appear here...")

    def append_log(self, text: str) -> None:
        self.appendPlainText(text)
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self) -> None:
        self.clear()
